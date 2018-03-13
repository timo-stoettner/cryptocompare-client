
# Cryptocompare Client

This is an unofficial Python client for the cryptocurrency data API of CryptoCompare. It supports both the public REST API and the websocket API.

To learn more about the official API, go to https://www.cryptocompare.com/api or https://min-api.cryptocompare.com/.




## Installation

```
pip install cryptocompare-client
```


## Usage

Initialize the client as follows:

```
from cryptocompare_client import CryptocompareClient
client = CryptocompareClient()
```
---
### REST API

The following wrappers for the rest-style API are implemented. All methods return a dict from the parsed JSON if the call was successful or the HTTP status code otherwise. (Note that while the HTTP call might be successful, the API can still return "Error" as a response, for instance due to invalid arguments.)

#### Coin List
Return coin list, see https://www.cryptocompare.com/api/#-api-data-coinlist-
```
response = client.get_coin_list()
```

#### Coin Snapshot
Return coin snapshot, see https://www.cryptocompare.com/api/#-api-data-coinsnapshot-
```
response = client.get_coin_snapshot("BTC","EUR")
```
Get coin snapshot for currency pair.

#### Top Pairs
Return top currency pairs by volume, see https://www.cryptocompare.com/api/#-api-data-toppairs-
```
response = client.get_top_pairs('BTC')
```

You can also set a different limit for number of top pairs returned (default is 2000):

```
response = client.get_top_pairs('BTC', limit=10)
```

#### Query any other API method
You can query any other API method on https://min-api.cryptocompare.com/ by calling `query_rest_api`:

```
client.query_rest_api('histoday', fsym='BTC', tsym='USD', limit=100)
```
The first parameter is the name of the API and all further parameters are the ones that are passed to the API call. See https://min-api.cryptocompare.com/ for all accepted parameters.
 
#### Helper methods
The following helper methods are implemented:

##### get_all_coins()
Return a list of all coins that are available on CryptoCompare
```
response = client.get_all_coins()
```
##### get_all_exchanges()
Return a list of all exchanges that trade a currency pair
```
response = client.get_all_exchanges('BTC','EUR')
```

#### Set different  base_url
All methods listed above take an optional argument `base_url` that you can set to use a different URL for the API requests. This should only be necessary if CryptoCompare changes the URL of the API.

For instance, you can set a new URL to retrieve the coin list from by calling

```
client.get_coin_list(base_url="https://www.my-new-crytocompare-url.com")
```
---
### Websocket API

#### Subscribe
In order to subscribe to a websocket, call the `subscribe` method:

```
client.subscribe('TRADE', 'GDAX', ('ETH','EUR')) 
```

The first parameter is the subscribe method. Accepted methods are 'TRADE', 'CURRENT', 'CURRENTAGG' or the respective integer value associated with the method. The second parameter takes the name of the exchange. The third parameter is a tuple of the currency pair.

As a shorthand you can also a pass a list of subscription strings in the format `{SubscriptionId}~{ExchangeName}~{FromSymbol}~{ToSymbol}`:

```
subs = ['2~Cryptsy~BTC~USD','2~BTCChina~BTC~USD', '2~Bitstamp~BTC~USD']
client.subscribe(sub_strings=subs) 
```

See https://www.cryptocompare.com/api/#-api-web-socket-subscribe- for more information.

#### Start listening
In order to start listening to the websocket, call `listen`:
```
client.listen()
```
You can also set an optional parameter to stop listening after a specified number of seconds:
```
client.listen(seconds=60)
```
By default, this will print the received messages to the shell.

#### Save messages to MongoDB
When initializing the client, you can pass an optional parameter `mongo_col` that points to a mongodb collection. When specified, all messages received from the websocket will automatically be stored in the collection. (This is currently only implemented for webocket messages, not for the Rest API. If you want to store messages received from the Rest API, you'd have to handle this yourself.)

```
from pymongo import MongoClient

mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client.cryptocurrency_database
my_collection = db.my_collection

client = CryptocompareClient(mongo_col=my_collection)
``` 

#### Handle incoming messages
If you want to handle incoming messages yourself, e.g. in order to store them in a different kind of database or to add some information such as the timestamp before storing them, you can override the method `process_message`:

```
class MyCCClient(CryptocompareClient):
    def process_message(self, msg):
        msg['timestamp'] = time.time()
        return msg 

client = MyCCClient()
``` 

---

