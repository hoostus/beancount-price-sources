import datetime
import logging
import io
from urllib import error
import xml.etree.ElementTree as ET

import pytz
import pandas

from decimal import Decimal as D
import beanprice.source
import beanprice.net_utils

"""
bean-price -e 'USD:rba/AUD'

Based on data from https://www.rba.gov.au/statistics/frequency/exchange-rates.html

The latest is published as RSS: https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml
Historical is a set of XLS/CSV https://www.rba.gov.au/statistics/historical-data.html#exchange-rates
"""

class Source(beanprice.source.Source):
    "Reserve Bank of Australia exchange rate fetcher. Currently only supports USD:AUD."

    # TODO: This is hard coded to fetch the AUD/USD rate pair. The RBA data is reversed
    # from how Beancount expects it so I'm unsure how to handle that. That is, the RBA
    # data tell you how much AUD for one foreign currency. That means the "ticker" is always
    # going to be AUD here.
    # I could maybe do something with bean-prices inverse ^ thing...?
    def get_latest_price(self, ticker):
        response = self.get_url('https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml')
        decoded_response = response.read().decode('utf-8')
        tree = ET.parse(io.StringIO(decoded_response))

        root = tree.getroot()
        prefix_map = {"r1": "http://purl.org/rss/1.0/",
                      "cb": "http://www.cbwiki.net/wiki/index.php/Specification_1.2/"}

        sydney_tz = pytz.timezone('Australia/Sydney')
        for exchangeRate in root.findall('.//r1:item/cb:statistics/cb:exchangeRate', prefix_map):
            targetCurrency = exchangeRate.find('./cb:targetCurrency', prefix_map).text
            value = exchangeRate.find('./cb:observation/cb:value', prefix_map).text
            period = exchangeRate.find('./cb:observationPeriod/cb:period', prefix_map).text
            # The times are always from 4pm Sydney time...
            observation_date = datetime.datetime.strptime(period, '%Y-%m-%d').replace(tzinfo=sydney_tz).replace(hour=16)

            if targetCurrency == 'USD':
                return beanprice.source.SourcePrice(D(value).quantize(D('1.0000')), observation_date, 'USD')

        return None

    def get_url(self, url):
        logging.info("Fetching %s", url)

        try:
            response = beanprice.net_utils.retrying_urlopen(url)
            if response is None:
                return None
            else:
                return response
        except error.HTTPError:
            return None


    def get_historical_price(self, ticker, date):
        """See contract in beancount.prices.source.Source."""

        if date.year >= 2023:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2023-current.xls'
        elif 2022 >= date.year >= 2018:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2018-2022.xls'
        elif 2017 >= date.year >= 2014:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2014-2017.xls'
        elif 2013 >= date.year >= 2010:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2010-2013.xls'
        elif 2009 >= date.year >= 2007:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2007-2009.xls'
        elif 2006 >= date.year >= 2003:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/2003-2006.xls'
        elif 2002 >= date.year >= 1999:
            xls = 'https://www.rba.gov.au/statistics/tables/xls-hist/1999-2002.xls'
        else:
            return None

        # Keep data as strings for now because we want them as Decimals and not floats
        rates = pandas.read_excel(xls, header=0, skiprows=range(10), index_col=0, parse_dates=True, dtype=str)
        # All rates are 4pm Sydney time, so add that information to pandas.
        rates.index = rates.index.tz_localize('Australia/Sydney')
        rates.index += pandas.DateOffset(hours=16)

        usd = rates['FXRUSD']

        iloc_idx = usd.index.get_indexer([date], method='nearest')
        closest_value = usd.iloc[iloc_idx]
        closest_date = closest_value.index.to_pydatetime()[0]
        rate = D(closest_value.iloc[0])
        return beanprice.source.SourcePrice(rate, closest_date, 'USD')


if __name__ == '__main__':
    rba = Source()
    print(rba.get_latest_price('USD'))
    print(rba.get_historical_price('USD', datetime.datetime(2007, 1, 2, 0, 0, 0, 0, pytz.utc)))

