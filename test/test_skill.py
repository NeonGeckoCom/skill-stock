# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import unittest

from ovos_bus_client import Message
from neon_minerva.tests.skill_unit_test_base import SkillTestCase
from mock import patch

from neon_skill_stock.data_models import StockPriceInfo, StockPriceRequest
os.environ["TEST_SKILL_ENTRYPOINT"] = "skill-stock.neongeckocom"


class TestSkillMethods(SkillTestCase):
    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        self.assertIsInstance(self.skill.translate_co, dict)
        self.assertIsInstance(self.skill.preferred_market, str)

    def test_handle_stock_price(self):
        message = Message("test", {"company": "3m"})
        self.skill.handle_stock_price(message)
        self.skill.speak_dialog.assert_called_once()
        args = self.skill.speak_dialog.call_args
        self.assertEqual(args[0][0], "stock.price")
        data = args[1]["data"]
        self.assertEqual(data["symbol"], "MMM")
        self.assertEqual(data["company"], "3M Company")
        self.assertIsInstance(float(data["price"]), float)
        self.assertEqual(data["provider"], "Alpha Vantage")
        self.assertIsInstance(args[1]["data"], dict)

        # message = Message("test", {"company": "microsoft"})
        # self.skill.handle_stock_price(message)
        # args = self.skill.speak_dialog.call_args
        # self.assertEqual(args[0][0], "stock.price")
        # data = args[1]["data"]
        # self.assertEqual(data["symbol"], "MSFT")
        # self.assertEqual(data["company"], "Microsoft Corporation")
        # self.assertIsInstance(float(data["price"]), float)
        # self.assertEqual(data["provider"], "Alpha Vantage")
        # self.assertIsInstance(args[1]["data"], dict)

    def test_search_company(self):
        # TODO
        pass

    def test_extract_company(self):
        test_ms = "what is microsoft trading at"
        test_google = "what is the stock price for google"
        test_apple = "what is apple stock valued at"
        test_amazon = "tell me about amazon stock"
        self.assertEqual(self.skill._extract_company(test_ms), "microsoft")
        self.assertEqual(self.skill._extract_company(test_google), "google")
        self.assertEqual(self.skill._extract_company(test_apple), "apple")
        self.assertEqual(self.skill._extract_company(test_amazon), "amazon")

    @patch("neon_skill_stock.request_backend")
    def test_get_stock_price(self, request_backend):
        request_backend.return_value = {
            "Global Quote": {
                "01. symbol": "TEST",
                "02. open": "145.6600",
                "03. high": "147.4700",
                "04. low": "145.1900",
                "05. price": "146.9200",
                "06. volume": "72398800",
                "07. latest trading day": "2023-07-21",
                "08. previous close": "145.3800",
                "09. change": "1.5400",
                "10. change percent": "1.0592%",
            }
        }
        
        price_data = self.skill.get_stock_price(StockPriceRequest(symbol="TEST"))
        request_backend.assert_called_once_with("/proxy/stock/quote", {"symbol": "TEST"})
        self.assertIsInstance(price_data, StockPriceInfo)
        self.assertEqual(price_data.symbol, "TEST")
        self.assertEqual(price_data.price, 146.92)
        self.assertEqual(price_data.provider, "Alpha Vantage")


if __name__ == '__main__':
    unittest.main()
