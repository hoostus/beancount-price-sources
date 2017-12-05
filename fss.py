"""Fetch prices from Morningstar's JSON 'api'
"""

import datetime
import logging
import re
import io
import csv
import string
from urllib import parse
from urllib import error

from beancount.core.number import D
from beancount.prices import source
from beancount.utils import net_utils

"""
bean-price -e 'AUD:fss/International_Equities'
"""

class Source(source.Source):
    "First State Super price extractor."

    def get_latest_price(self, ticker):
        return self.get_historical_price(ticker, datetime.date.today())

    def get_csv(self, date):
        template = 'https://firststatesuper.com.au/content/dam/ftc/superunitprices/super-{0:0>2}-{1}.csv'
        url = template.format(date.month, date.year)
        logging.info("Fetching %s", url)

        try:
            response = net_utils.retrying_urlopen(url)
            if response is None:
                return None
            else:
                return response
        except error.HTTPError:
            return None

    def get_historical_price(self, ticker, date):
        """See contract in beancount.prices.source.Source."""

        fund_name = ticker.replace('_', '').lower()

        response = self.get_csv(date)
        if not response:
            # We may need to check the previous month to find the most recent
            # unit price. e.g. if we run this on December 1st on a Sunday, there
            # won't be a December CSV yet.
            response = self.get_csv(date + datetime.timedelta(weeks=-1))
            if not response:
                # But only check 1 month previous. If that still didn't work
                # then give up.
                return None

        decoded_response = response.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(decoded_response))

        for row in csv_reader:
            fund = row[0].lower().replace(' ', '')
            if fund == 'investmentoptions':
                dates = [datetime.datetime.strptime(x, '%d/%m/%Y') for x in row[1:]]
            if fund == fund_name:
                prices = [D(x) for x in row[1:]]

        dt_date = datetime.datetime(date.year, date.month, date.day)
        for (trade_date, price) in zip(dates, prices):
            if trade_date <= dt_date:
                return source.SourcePrice(price, trade_date, None)

        # If the date we wanted was at the beginning of the month...and falls on a day
        # that was a weekend/holiday then we need to look in the previous month's
        # CSV file to find the closest price.
        new_date = date.replace(day=1) + datetime.timedelta(days=-1)
        return self.get_historical_price(ticker, new_date)

