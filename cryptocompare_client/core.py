# -*- coding: utf-8 -*-
import logging
import time

from requests.exceptions import ConnectionError
from threading import Thread

import pymongo
import requests
import json
import sys

import socketIO_client

from . import masks
from . import customized_methods

setattr(socketIO_client.transports.XHR_PollingTransport,
        'recv_packet', customized_methods.custom_recv_packet)


class CryptocompareClient(object):
    def __init__(self, sub_strings=None, websocket_url='https://streamer.cryptocompare.com',
                 mongo_col=None, namespace=None):
        """CryptocompareClient connects to the Websocket and Rest APIs of Cryptocompare.

        Args:
            sub_strings (optional): Websocket subscriptions, defaults to None.
                The strings must have the format
                '{SubscriptionId}~{ExchangeName}~{FromSymbol}~{ToSymbol}'
                sub_strings must either be a list of strings or a single strings

            websocket_url (optional): The url used to connect to the websocket.
                Defaults to 'https://streamer.cryptocompare.com'

            mongo_col (optional): MongoDB (pymongo) collection to insert messages into.
                Defaults to None

            namespace (optional): socketIO Namespace used to handle events.
                Defaults to None.
        """

        if isinstance(sub_strings, basestring):
            sub_strings = [sub_strings]

        if isinstance(sub_strings, list):
            self.sub_strings = sub_strings[:]
        else:
            self.sub_strings = sub_strings

        self.url = websocket_url
        self.mongo_col = mongo_col
        self.namespace = namespace
        self.restart_after = None

        self._init_websocket()


    def _init_websocket(self):

        if self.namespace is None:
            self.socket = socketIO_client.SocketIO(self.url)
        else:
            self.socket = socketIO_client.SocketIO(self.url, Namespace=self.namespace)

        self.socket.on('m', self._on_message)

        if self.sub_strings is not None:
            self.subscribe(sub_strings=self.sub_strings[:])


    def restart(self):
        """Restart websocket"""
        logging.info("Restarting Cryptocompare Client...")
        self.stop()

        if hasattr(self, "thread"):
            self.thread.join()

        self._init_websocket()
        self.listen(self.seconds, self.restart_after)


    def listen(self, seconds=None, restart_after=None):
        """Start listening to the websocket.

        Args:
            seconds: Number of seconds to listen. Defaults to None.
                If not specified, client will listen forever.

            restart_after: Number of seconds to wait until restart,
                when no messages are received. If not specified,
                client will not restart.

        """
        self.seconds = seconds
        self.restart_after = restart_after
        self.start_time = time.time()
        self.received_messages = []

        if restart_after is None:
            if self.seconds is not None:
                self.socket.wait(seconds=seconds)
            else:
                self.socket.wait()
        else:
            def _wait_thread():
                if self.seconds is not None:
                    self.socket.wait(seconds=seconds)
                else:
                    self.socket.wait()

            self.thread = Thread(target=_wait_thread)
            self.thread.start()

            try:
                if restart_after is not None:
                    time.sleep(restart_after)
                while True:
                    n_messages = len(filter(lambda message_time:
                                            time.time()-message_time < restart_after,
                                            self.received_messages))

                    logging.debug("Number of messages in last %s seconds: %s",
                                  restart_after, n_messages)

                    if restart_after is not None:
                        if n_messages == 0:
                            self.restart()
                            break
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.debug("KeyboardInterrupt: Stopping...")
                self.stop()
                self.thread.join()


    def stop(self):
        """Disconnect websocket"""
        self.socket.disconnect()


    def get_coin_list(self, base_url='https://www.cryptocompare.com/api/data/'):
        """Return coin list, see https://www.cryptocompare.com/api/#-api-data-coinlist-"""
        r = requests.get('{}coinlist/'.format(base_url))
        if r.status_code == 200:
            return r.json()
        else:
            return r.status_code

    def get_coin_snapshot(self, fsym, tsym, base_url='https://www.cryptocompare.com/api/data/'):
        """Return coin snapshot, see https://www.cryptocompare.com/api/#-api-data-coinsnapshot-"""
        r = requests.get('{}coinsnapshot/?fsym={}&tsym={}'.format(base_url,fsym,tsym))
        if r.status_code == 200:
            return r.json()
        else:
            return r.status_code

    def get_top_pairs(self, fsym, limit=2000, base_url='https://min-api.cryptocompare.com/data/'):
        """Return top currency pairs by volume, see https://www.cryptocompare.com/api/#-api-data-toppairs-"""
        r = requests.get('{}top/pairs?fsym={}&limit={}'.format(base_url, fsym, limit))
        if r.status_code == 200:
            return r.json()
        else:
            return r.status_code

    def get_all_coins(self, base_url='https://www.cryptocompare.com/api/data/'):
        """Return a list of all coins that are available on CryptoCompare"""
        coin_list = self.get_coin_list(base_url=base_url)
        return [coin for coin,d in coin_list['Data'].iteritems()]


    def get_all_exchanges(self, fsym, tsym, base_url='https://www.cryptocompare.com/api/data/'):
        """Return a list of all exchanges that trade a currency pair"""
        res = self.get_coin_snapshot(fsym, tsym, base_url=base_url)
        try:
            exchanges = res['Data']['Exchanges']
            markets = [x['MARKET'] for x in exchanges]
            return sorted(markets)
        except KeyError:
            return res

    def query_rest_api(self, api_name, base_url='https://min-api.cryptocompare.com/data/', **params):
        """Query the Rest API with specified params"""
        query_params = '&'.join(['{}={}'.format(k,v) for k,v in params.iteritems()])
        query_string = base_url + api_name + '?' + query_params
        r =  requests.get(query_string)
        if r.status_code == 200:
            return r.json()
        else:
            return r.status_code


    def subscribe(self, method=None, exchange=None, currency_pair=None, sub_strings=None):
        """Subscribe to websocket channels

        The channels must either be specified by the parameter sub_strings or by a combination
        of the parameters method, exchange and currency_pair.

        Args:
            method (optional): The method must either be 'TRADE', 'CURRENT', 'CURRENTAGG' or
                one of the corresponding SubsciptionIDs (0, 2 or 5).
                See https://www.cryptocompare.com/api/#-api-web-socket-subscribe- for more
                information.

            exchange (optional): A valid exchange name that is recognized by the cryptocompare API.

            currency_pair (optional): A tuple of currency symbols that are recognized by the
                cryptocompare API, such as ('BTC','USD')

            sub_strings (optional): Subscription strings in the format
                '{SubscriptionId}~{ExchangeName}~{FromSymbol}~{ToSymbol}'.
                sub_strings must either be a list of strings or a single string-
        """
        if method is None and exchange is None and currency_pair is None and sub_strings is None:
            raise ValueError("Either sub_strings or method, exchange, and currency_pair must be specified.")
        elif sub_strings is not None:
            if method is not None or exchange is not None or currency_pair is not None:
                raise ValueError("If sub_strings is specified, all other keyword arguments must be None.")
            if isinstance(sub_strings, basestring):
                sub_strings = [sub_strings]
        elif method is None or exchange is None or currency_pair is None:
            raise ValueError("If sub_strings is None, all other keyword arguments must be specified.")
        else:
            method = self._convert_method_to_number(method)
            sub_strings = ['{}~{}~{}~{}'.format(method,
                                              exchange,
                                              currency_pair[0],
                                              currency_pair[1])]


        if self.sub_strings is None:
            self.sub_strings = []

        self.sub_strings.extend(sub_strings)
        self.sub_strings = list(set(self.sub_strings))

        try:
            self.socket.emit('SubAdd', { 'subs': sub_strings })
        except ConnectionError as e:
            logging.info("ConnectionError: %s", e)
            self.restart()


    def unsubscribe(self, method=None, exchange=None, currency_pair=None, sub_strings=None):
        """Unubscribe from websocket channels

        The channels must either be specified by the parameter sub_strings or by a combination
        of the parameters method, exchange and currency_pair.

        Args:
            method (optional): The method must either be 'TRADE', 'CURRENT', 'CURRENTAGG' or
                one of the corresponding SubsciptionIDs (0, 2 or 5).
                See https://www.cryptocompare.com/api/#-api-web-socket-subscribe- for more
                information.

            exchange (optional): A valid exchange name that is recognized by the cryptocompare API.

            currency_pair (optional): A tuple of currency symbols that are recognized by the
                cryptocompare API, such as ('BTC','USD')

            sub_strings (optional): Subscription strings in the format
                '{SubscriptionId}~{ExchangeName}~{FromSymbol}~{ToSymbol}'.
                sub_strings must either be a list of strings or a single string-
        """

        if sub_strings is not None:
            if isinstance(sub_strings, basestring):
                sub_strings = [sub_strings]
            self.socket.emit('SubRemove', { 'subs': sub_strings })
        else:
            method = self._convert_method_to_number(method)

            sub_strings = ['{}~{}~{}~{}'.format(method,
                                              exchange,
                                              currency_pair[0],
                                              currency_pair[1])]

        self.socket.emit('SubRemove', { 'subs': sub_strings })


    def unsubscribe_all(self):
        """Unsubscribe from all channels that have been subscribed"""
        self.socket.emit('SubRemove', { 'subs': self.sub_strings })


    def _convert_method_to_number(self, method):
        """Convert method name to corresponding SubscriptionId"""
        if str(method).upper() not in ['0', '2', '5', 'TRADE', 'CURRENT', 'CURRENTAGG']:
            raise ValueError('Method has invalid value: {}'.format(method))

        if str(method).upper() == 'TRADE' :
            method = '0'
        elif str(method).upper() == 'CURRENT':
            method = '2'
        elif str(method).upper() == 'CURRENTAGG':
            method = '5'

        return method


    def _parse_message(self, response):
        """Parse a message received through websocket and return dictionary

        Args:
            response (str): The raw message
        """

        response_list = response.split('~')
        sub_id = response_list[0]

        try:
            if sub_id == '0': # TRADE
                keys = ['SubscriptionId','ExchangeName','CurrencySymbol','CurrencySymbol','Flag','TradeId','TimeStamp','Quantity','Price','Total']
                res = dict(zip(keys, response_list))

            elif sub_id == '2' or sub_id == '5': # CURRENT / CURRENTAGG
                unpacked = {}
                mask = int(response_list[-1], 16)
                i = 0
                for key,value in masks.current:
                    if value == 0 or mask & value:
                        unpacked[key] = response_list[i]
                        i += 1
                res = unpacked
            else:
                logging.debug("Unknown sub_id in message: %s", response)
                res = None
        except:
            logging.warning("Parsing failed for: %s", response)
            res = None

        return res


    def _on_message(self, *args):
        """Handle received messages and write to MongoDB if mongo_col was specified"""

        parsed_message = self._parse_message(args[0])

        if parsed_message is None:
            logging.debug(("Could not parse message: %s", args[0]))
            return

        logging.debug("Received message: %s", parsed_message)

        parsed_message = self.process_message(parsed_message)

        if self.mongo_col is not None:
            self.mongo_col.insert_one(parsed_message)



    def process_message(self, msg):
        """Override this method to alter or handle incoming messages"""
        if self.mongo_col is None:
            print msg
        return msg
