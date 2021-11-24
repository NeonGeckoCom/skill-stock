# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Authors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3
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
#
# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests

from time import sleep
# from adapt.intent import IntentBuilder
# from mycroft.skills import intent_handler
from neon_utils.skills.neon_skill import NeonSkill, LOG


class StockSkill(NeonSkill):
    def __init__(self):
        super(StockSkill, self).__init__("StockSkill")
        self.preferred_market = "United States"
        self.translate_co = {"3 m": "mmm",
                             "3m": "mmm",
                             "coca cola": "ko",
                             "coca-cola": "ko",
                             "google": "goog",
                             "exxonmobil": "xom"}

        self.service = self.settings.get('service') or "Alpha Vantage"
        self.api_key = self.settings.get('api_keys', {}).get(self.service) or self.settings.get("api_key")

        if self.service == "Financial Modeling Prep" and not self.api_key:
            self.service = "Alpha Vantage"
            self.update_skill_settings({"service": self.service}, skill_global=True)

        if self.service == "Alpha Vantage":
            from neon_utils.service_apis import alpha_vantage
            self.data_source = alpha_vantage

    def initialize(self):
        if self.data_source:
            self.register_intent_file("StockPrice.intent", self.handle_stock_price_intent)
        else:
            LOG.error(f"No sata provider specified; skill will be disabled!")

    # @intent_handler(IntentBuilder("").require("StockPriceKeyword").require("Company"))
    def handle_stock_price_intent(self, message):
        company = message.data.get("company")
        LOG.debug(company)

        # Filter out articles from company name
        if str(company).split()[0] in ["of", "for", "what"]:
            LOG.warning('fixing string')
            company = " ".join(str(company).split()[1:])
            if company.split()[0] == "is":
                LOG.warning('fixing string is')
                company = " ".join(str(company).split()[1:])
            LOG.debug(company)
        # Filter out "stock" keyword from company name
        if company and company.strip().endswith(" stock"):
            LOG.warning("Stripping 'stock' from company name")
            company = company.strip().rstrip(" stock")

        try:
            # Special case handling for 3m
            if company == 'm' and "3m" in str(message.data['utterance']).split():
                company = "mmm"

            # Special case handling for common brands that don't match accurately
            if company in self.translate_co.keys():
                company = self.translate_co[company]
                LOG.debug(company)

            match_data = self.search_company(company)
            company = match_data.get("name")
            symbol = match_data.get("symbol")
            LOG.debug(f"found {company} with symbol {symbol}")
            if symbol:
                quote = self.get_stock_price(symbol)
            else:
                quote = None
            if not all([symbol, company, quote]):
                self.speak_dialog("not.found", data={'company': company})
            else:
                response = {'symbol': symbol,
                            'company': company,
                            'price': quote,
                            'provider': self.service}
                self._mark_1_info_on_speech(response['symbol'], response['price'])
                self.speak_dialog("stock.price", data=response)
                if self.gui_enabled:
                    self.gui["title"] = company
                    self.gui["text"] = f"${quote}"
                    self.gui.show_page("Stock.qml")
                    self.clear_gui_timeout()
            sleep(12)
            self._mark_1_display_release()

        except requests.HTTPError as e:
            self.speak_dialog("api.error", data={'error': str(e)})
        except Exception as e:
            self.log.exception(e)
            if self.voc_match(message.data["utterance"], "StockPriceKeyword"):
                self.speak_dialog("not.found", data={'company': company})

    def search_company(self, company: str) -> dict:
        """
        Find a traded company by name
        :param company: Company to search
        :return: dict company data: `symbol`, `name`, `region`, `currency`
        """
        kwargs = {"region": self.preferred_market}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        stocks = self.data_source.search_stock_by_name(company, **kwargs)
        LOG.debug(f"stocks={stocks}")
        return stocks[0]

    def get_stock_price(self, symbol: str):
        """
        Get the current trade price by ticker symbol
        :param symbol: Ticker symbol to query
        :return:
        """
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        stock_data = self.data_source.get_stock_quote(symbol)
        if not stock_data.get("price"):
            return None
        return str(round(float(stock_data.get("price")), 2))

    def _mark_1_info_on_speech(self, symbol, price):
        """
        Show the ticker symbol and price on the Mark-1 display when speaking
        """
        # When speech starts, output the information on the Mark-1 display
        self.bus.once("recognizer_loop:audio_output_start",
                      self.enclosure.mouth_text("{}: {}".format(symbol, price))
                      )
        self.enclosure.deactivate_mouth_events()

    def _mark_1_display_release(self):
        """
        Reset Mark-1 display if it was taken by the skill.
        """
        self.enclosure.activate_mouth_events()
        self.enclosure.mouth_reset()


def create_skill():
    return StockSkill()
