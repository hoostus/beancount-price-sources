Additional importers for beancount plaintext accounting

Installation
------------
python setup.py install 

Morningstar price source
------------------------
bean-price -e 'USD:hoostus_sources.morningstar/etfs:XASX:VEU'

The Morningstar ticker is 3 parts: the "type", the exchange,
and then the actual ticker. This mimics the URL structure on the
Morningstar website when you search for a quote.

That is, is you search for Microsoft, you will be redirected to the
URL:

http://beta.morningstar.com/stocks/xnas/msft/quote.html

Which becomes stocks:XNAS:MSFT for use with this price source.

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
