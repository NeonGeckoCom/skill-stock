# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
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

from neon_utils.skills.neon_skill import NeonSkill
from neon_api_proxy.client import alpha_vantage
from adapt.intent import IntentBuilder
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements

from mycroft.skills import intent_handler


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
        self._service = None

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    @property
    def service(self):
        if not self._service:
            service = self.settings.get('service') or "Alpha Vantage"
            if service == "Financial Modeling Prep" and not self.api_key:
                service = "Alpha Vantage"
            self._service = service
        return self._service

    @property
    def api_key(self):
        return self.settings.get('api_keys', {}).get(self.service) or \
               self.settings.get("api_key")

    @property
    def data_source(self):
        return alpha_vantage

    @intent_handler(IntentBuilder("StockPrice").require("share_price")
                    .require("Company"))
    def handle_stock_price(self, message):
        """
        Handle a query for stock value
        """
        company = message.data.get("Company").lower().strip()
        LOG.debug(company)

        # TODO: Generalize parsing for language support
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
            # # Special case handling for 3m
            # if company == 'm' and "3m" in str(message.data['utterance']).split():
            #     company = "mmm"

            # Special case for common stocks that don't match accurately
            if company in self.translate_co:
                company = self.translate_co[company]
                LOG.debug(company)

            match_data = self._search_company(company)
            company = match_data.get("name")
            symbol = match_data.get("symbol")
            LOG.debug(f"found {company} with symbol {symbol}")
            if symbol:
                quote = self._get_stock_price(symbol)
            else:
                quote = None
            if not all([symbol, company, quote]):
                self.speak_dialog("not.found", data={'company': company})
            else:
                response = {'symbol': symbol,
                            'company': company,
                            'price': quote,
                            'provider': self.service}
                self.speak_dialog("stock.price", data=response)
                self.gui["title"] = company
                self.gui["text"] = f"${quote}"
                self.gui.show_page("Stock.qml")
        except Exception as e:
            LOG.exception(e)
            self.speak_dialog("not.found", data={'company': company})

    def _search_company(self, company: str) -> dict:
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
        # TODO: Catch and warn on API error here
        return stocks[0]

    def _get_stock_price(self, symbol: str):
        """
        Get the current trade price by ticker symbol
        :param symbol: Ticker symbol to query
        :return:
        """
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        stock_data = self.data_source.get_stock_quote(symbol)
        # TODO: Catch and warn on API error here
        if not stock_data.get("price"):
            return None
        return str(round(float(stock_data.get("price")), 2))


def create_skill():
    return StockSkill()
