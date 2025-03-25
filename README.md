Additional importers for beancount plaintext accounting

Installation
------------
python setup.py install 

First State Super
-----------------
bean-price -e 'AUD:hoostus_sources.fss/International_Equities'

First State Super is an Australian Superannuation fund that
publishes unit prices daily. 

There are no tickers, per se, for First State Super funds. They
just have normal names like "International Equities".

Replace any spaces with underscores, so "International Equities"
becomes "International_Equities".

OpenExchange
------------
bean-price -e 'VND:hoostus_sources.openexchange/<app_id>:USD_VND'

OpenExchange provides exchange rates, though you must sign up in order
to use the service. Sign ups are free. After you sign up, you will get
an app_id.

The app_id forms part of the "ticker".

Reserve Bank of Australia (RBA)
-------------------------------
bean-price -e 'USD:hoostus_sources.rba/AUD'

This allows Australians to fetch the "official" exchange rate
(i.e. as required by the ATO).

Currently only supports USD:AUD.

IBKR
----
Fetch prices from Interactive Brokers. This is forked from
taroich's original work at https://tariochbctools.readthedocs.io/en/latest/price_fetchers.html

## Configuration

We need to get an IBKR_TOKEN and IBKR_QUERY_ID from Interactive Brokers. Here's how to set
things up and find them.

You need to configure a Flex Query on IBKR with your Open Positions.

1. Create a Flex Query. Go to "Performance & Reports -> Flex Queries".
1. Click the "+" button in the "Activity Flex Query" box to create a new one.
1. Give it a name. Something like "Open Positions for Beancount".
1. Select the "Open Positions" option. It will pop up a dialog to select which details you want for the open positions.
1. Select "Currency", "Symbol", "Report Date", and "Mark Price". If you select other things you might run into issues with ibflex's parser failing; it seems to choke on unexpected fields.
1. Scroll down and change the "Date Format" to "yyyy-MM-dd" (nb I'm not 100% sure this is necessary to make ibflex work but I'm not too lazy to check.)
1. Change the "Time Format" to "HH:mm:ss" (nb ditto)
1. Click "Continue" and then "Create".

Now you've got the Flex Query created, we need to get the details for the price fetcher.

Click on the &#9432; ("i" in a circle; information) to the left of your Flex Query. This will pop up a dialog. The first item is the "Query ID". Make note of that.
Put it in your environment variables (e.g. using direnv or similar) as IBKR_QUERY_ID.

Next we need to enable and configure the Flex Web Service Configuration. It's a box on the bottom right. Click the gear icon to configure it.
Make sure it is enabled. A "Current Token" needs to saved as the environment variable IBKR_TOKEN. "Activation Period" will show you how long
the token is valid for. I think the default is one year. You can always change it to something else and generate a new token (and then
update your IBKR_TOKEN environment variable).
