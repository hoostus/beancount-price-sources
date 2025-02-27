"""Fetch prices from Morningstar's JSON 'api'
"""

import datetime
import logging
import io
import csv
from urllib import error

from decimal import Decimal as D
import beanprice.source
import beanprice.net_utils

"""
bean-price -e 'AUD:fss/International_Shares'
"""

class Source(beanprice.source.Source):
    "First State Super price extractor."

    def get_latest_price(self, ticker):
        return self.get_historical_price(ticker, datetime.date.today())

    def get_csv(self):
        url = 'https://aware.com.au/bin/unitPriceExport?category=FUTURE_SAVER'
        logging.info("Fetching %s", url)

        try:
            response = beanprice.net_utils.retrying_urlopen(url, timeout=10)
            if response is None:
                return None
            else:
                return response
        except error.HTTPError:
            return None

    def get_historical_price(self, ticker, date):
        """See contract in beancount.prices.source.Source."""

        fund_name = ticker.replace('_', ' ')

        response = self.get_csv()

        decoded_response = response.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_response))

        current_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        dt_date = datetime.datetime(date.year, date.month, date.day).replace(tzinfo=current_tz)

        for row in csv_reader:
            r_date = datetime.datetime.strptime(row['Date'], '%d/%m/%Y').replace(tzinfo=current_tz)
            if r_date <= dt_date:
                r_price = row[fund_name]
                return beanprice.source.SourcePrice(D(r_price), r_date, None)

        return None

if __name__ == '__main__':
    fss = Source()
    print(fss.get_latest_price('International_Shares'))
    print(fss.get_historical_price('International_Shares', datetime.datetime(2025, 1, 1)))

