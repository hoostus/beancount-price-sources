"""Fetch prices from Morningstar's JSON 'api'
"""

import datetime
import logging
import re
import json
from bs4 import BeautifulSoup
from urllib import parse
from urllib import error

from beancount.core.number import D
from beancount.prices import source
from beancount.utils import net_utils

"""
bean-price -e 'USD:morningstar/etfs:ARCX:GSLC'
bean-price -e 'USD:morningstar/stocks:NYSE:GE'
bean-price -e 'AUD:morningstar/etfs:XASX:VEU'
"""


class Source(source.Source):
    "Morningstar API price extractor."

    def get_latest_price(self, ticker):
        return self.get_historical_price(ticker, datetime.date.today())

    def get_morningstar_secid(self, security_type, exchange, ticker):
        template = 'http://beta.morningstar.com/{}/{}/{}/quote.html'
        url = template.format(security_type, exchange, ticker)
        try:
            response = net_utils.retrying_urlopen(url)
            if response is None:
                return None
            response = response.read().decode('utf-8').strip()
        except error.HTTPError:
            return None

        soup = BeautifulSoup(response, 'html.parser')
        
        def make_finder(name):
            def meta_finder(a):
                return a.name == 'meta' and 'name' in a.attrs and a['name'] == name
            return meta_finder

        def get_meta(name):
            attr = soup.find_all(make_finder(name))[0]
            return attr['content']

        fetched_exchange_id = get_meta('exchangeId')
        fetched_ticker = get_meta('ticker')
        sec_id = get_meta('secId')

        return sec_id

    def get_historical_price(self, compound_ticker, date):
        """See contract in beancount.prices.source.Source."""

        security_type, exchange, ticker = compound_ticker.lower().split(':')
        sec_id = self.get_morningstar_secid(security_type, exchange, ticker)

        if not sec_id:
            logging.info("Could not find secId for %s:%s:%s" % (security_type, exchange, ticker))
            return None

        # Look back some number of days in the past in order to make sure we hop
        # over national holidays.
        begin_date = date - datetime.timedelta(days=5)
        end_date = date

        template = 'http://mschart.morningstar.com/chartweb/defaultChart?type=getcc&secids={}&dataid={}&startdate={}&enddate={}&currency=&format=1'

        def fmt(d):
            return d.strftime('%Y-%m-%d')

        # The data_id is a magic number that tells the Morningstar backend
        # exactly what type of data you want. (i.e. price data, growth of $10,000,
        # and so on) For some reason it uses a different number when talking about
        # mutual funds vs etfs and stocks
        if security_type == 'funds':
            data_id = 8217
        else:
            data_id = 8225

        url = template.format(sec_id, data_id, fmt(begin_date), fmt(end_date))
        logging.info("Fetching %s", url)

        current_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        def hook(dct):
            """ An ad-hoc parser for Morningstar's weird format. """
            if 'code' in dct:
                return {'code': int(dct['code']),
                        'message': dct['message']}
            elif set(dct.keys()) == set(('i', 'd')):
                return {'i': int(dct['i']),
                        'd': dct['d']}
            elif set(dct.keys()) == set(('i', 'v')):
                return {'i': datetime.datetime.strptime(dct['i'], '%Y-%m-%d').replace(tzinfo=current_tz),
                        'v': D(dct['v'])}
            elif set(dct.keys()) == set(('i', 't')):
                return dct
            elif set(dct.keys()) == set('r'):
                return dct
            elif set(dct.keys()) == set(('data', 'status')):
                return dct
            else:
                return dct

        try:
            response = net_utils.retrying_urlopen(url)
            if response is None:
                return None
            response = response.read().decode('utf-8').strip()
            response = json.loads(response, object_hook=hook)
            data = response['data']
            status = response['status']
            if status['code'] != 200:
                logging.info("HTTP Status: [%s] %s" % (status['code'], status['message']))
                return None
        except error.HTTPError:
            return None

        try:
            last_price = data['r'][-1]['t'][-1]['d'][-1]
            price = last_price['v']
            trade_date = last_price['i']

            return source.SourcePrice(price, trade_date, None)
        except:
            import sys
            logging.error("Error parsing data.", sys.exc_info()[0])
            return None

