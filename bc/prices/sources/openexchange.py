"""Fetch prices from Morningstar's JSON 'api'
"""

import datetime
import logging
import re
import json
from urllib import parse
from urllib import error

from beancount.core.number import D
from beancount.prices import source
from beancount.utils import net_utils

"""
bean-price -e 'USD:openexchange/<app_id>:USD_VND'
"""

class Source(source.Source):
    "Morningstar API price extractor."

    def get_url(self, url_template, ticker):
        app_id, currencies = ticker.split(':')
        from_currency, to_currency = currencies.split('_')

        url = url_template.format(app_id, from_currency, to_currency)
        logging.info("Fetching %s", url)
        try:
            response = net_utils.retrying_urlopen(url)
            if response is None:
                return None
            response = response.read().decode('utf-8').strip()
            response = json.loads(response)
        except error.HTTPError:
            return None

        # we use quantize because otherwise the conversion from an float to a Decimal
        # leaves tons of cruft (i.e. dozens of digits of meaningless precision) that
        # just clutters up the price file
        price = D(response['rates'][to_currency]).quantize(D('1.000000'))
        trade_date = datetime.datetime.fromtimestamp(response['timestamp'])
        return source.SourcePrice(price, trade_date, from_currency)

    def get_historical_price(self, ticker, date):
        template = 'https://openexchangerates.org/api/historical/{}.json'.format(date.strftime('%Y-%m-%d'))
        template += '?app_id={}&base={}&symbols={}'
        return self.get_url(template, ticker)

    def get_latest_price(self, ticker):
        template = 'https://openexchangerates.org/api/latest.json?app_id={}&base={}&symbols={}'
        returnself.get_url(template, ticker)

