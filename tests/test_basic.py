# -*- coding: utf-8 -*-

from .context import cryptocompare_client

from requests.exceptions import ConnectionError, MissingSchema

import unittest


class RestTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        self.client = cryptocompare_client.CryptocompareClient()

    def test_coin_list_valid(self):
        res = self.client.get_coin_list()
        self.assertTrue(isinstance(res, dict))

    def test_coin_list_invalid(self):
        with self.assertRaises(ConnectionError):
            self.client.get_coin_list(base_url="http://some_wrong_url.com")

    def test_coin_list_invalid_url2(self):
        with self.assertRaises(MissingSchema):
            self.client.get_coin_list(base_url="some_wrong_url.com")

    def test_coin_snapshot_valid(self):
        res = self.client.get_coin_snapshot('BTC', 'EUR')
        self.assertTrue(isinstance(res, dict))

    def test_coin_snapshot_invalid_coins(self):
        res = self.client.get_coin_snapshot('WRONGONE', 'EUR')
        self.assertEqual(res['Response'], 'Error')

    def test_coin_snapshot_invalid_url(self):
        with self.assertRaises(ConnectionError):
            self.client.get_coin_snapshot('BTC', 'EUR', base_url="http://some_wrong_url.com")

    def test_top_pairs_valid(self):
        res = self.client.get_top_pairs('BTC')
        self.assertTrue(isinstance(res, dict))

    def test_top_pairs_invalid_url(self):
        with self.assertRaises(ConnectionError):
            self.client.get_top_pairs('BTC', base_url="http://some_wrong_url.com")

    def test_top_pairs_invalid_coin(self):
        res = self.client.get_top_pairs('WRONGONE')
        self.assertEqual(res['Response'], 'Error')

    def test_get_all_coins(self):
        res = self.client.get_all_coins()
        self.assertTrue(isinstance(res, list))
        self.assertTrue(len(res) > 10)

    def test_get_all_coins_invalid_url(self):
        with self.assertRaises(ConnectionError):
            self.client.get_all_coins(base_url="http://some_wrong_url.com")

    def test_get_all_exchanges(self):
        res = self.client.get_all_exchanges('ETH', 'EUR')
        self.assertTrue(isinstance(res, list))
        self.assertTrue(len(res) > 0)

    def test_get_all_exchanges_invalid_url(self):
        with self.assertRaises(ConnectionError):
            self.client.get_all_exchanges('ETH', 'EUR',base_url="http://some_wrong_url.com")

    def test_get_all_exchanges_invalid_coin(self):
        res = self.client.get_all_exchanges('WRONGONE', 'EUR')
        self.assertEqual(res['Response'], 'Error')


if __name__ == '__main__':
    unittest.main()
