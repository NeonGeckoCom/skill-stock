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

import re

from typing import Optional
from neon_skill_stock.data_models import StockPriceRequest, StockPriceInfo
from neon_utils.hana_utils import request_backend
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler, skill_api_method
from ovos_workshop.skills.common_query_skill import CommonQuerySkill, CQSMatchLevel


class StockSkill(CommonQuerySkill):
    def __init__(self, **kwargs):
        CommonQuerySkill.__init__(self, **kwargs)
        self.preferred_market = "United States"
        self.translate_co = {"3 m": "mmm",
                             "3m": "mmm",
                             "coca cola": "ko",
                             "coca-cola": "ko",
                             "google": "goog",
                             "exxonmobil": "xom"}

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

    @skill_api_method
    def get_stock_price(self, request: StockPriceRequest) -> StockPriceInfo:
        """
        Get the current stock price information for a given ticker symbol.
        """
        stock_data = request_backend("/proxy/stock/quote",
                                     {"symbol": request.symbol})
        return StockPriceInfo(**stock_data)

    @intent_handler("stock_price.intent")
    def handle_stock_price(self, message):
        """
        Handle a query for stock value
        """
        company = message.data.get("company").lower().strip()
        LOG.debug(company)

        try:
            # Special case for common stocks that don't match accurately
            if company in self.translate_co:
                LOG.info(f"{company} in {self.translate_co}")
                company = self.translate_co[company]

            match_data = self._search_company(company)
            if not match_data:
                self.speak_dialog("not.found", data={'company': company})
                return
            company = match_data.get("2. name")
            symbol = match_data.get("1. symbol")
            LOG.info(f"found {company} with symbol {symbol}")
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
                            'provider': "Alpha Vantage"}
                self.speak_dialog("stock.price", data=response)
                self.gui["title"] = company
                self.gui["text"] = f"${quote}"
                self.gui.show_page("Stock.qml")
        except Exception as e:
            LOG.exception(e)
            self.speak_dialog("not.found", data={'company': company})

    def CQS_match_query_phrase(self, phrase: str):
        company = self._extract_company(phrase)
        if not company:
            LOG.debug(f"no company found in {phrase}")
            return None
        try:
            match = self._search_company(company)
        except Exception as e:
            LOG.exception(e)
            return None
        if not match:
            LOG.info(f"not a company: {company}")
            return None
        company = match.get("2. name")
        symbol = match.get("1. symbol")
        try:
            quote = self._get_stock_price(symbol)
        except Exception as e:
            LOG.exception(e)
            return None

        response = {'symbol': symbol,
                    'company': company,
                    'price': quote,
                    'provider': "Alpha Vantage"}
        dialog = self.dialog_renderer.render("stock.price",
                                             response)
        callback_data = {"company": company, "quote": quote, "answer": dialog}
        return phrase, CQSMatchLevel.EXACT, dialog, callback_data

    def CQS_action(self, phrase: str, callback_data: dict):
        self.gui["title"] = callback_data.get("company")
        self.gui["text"] = f"${callback_data.get('quote')}"
        self.gui.show_page("Stock")

    def _search_company(self, company: str) -> Optional[dict]:
        """
        Find a traded company by name
        :param company: Company to search
        :return: dict company data: `symbol`, `name`, `region`, `currency`
        """
        kwargs = {"region": self.preferred_market,
                  "company": company}
        stocks = request_backend("/proxy/stock/symbol", kwargs)
        LOG.info(f"stocks={stocks}")
        if stocks and stocks.get("bestMatches"):
            return stocks["bestMatches"][0]
        else:
            return None

    @staticmethod
    def _get_stock_price(symbol: str):
        """
        Get the current trade price by ticker symbol
        :param symbol: Ticker symbol to query
        :return:
        """
        stock_data = request_backend("/proxy/stock/quote", {"symbol": symbol})
        price = stock_data.get("Global Quote", {}).get("05. price")
        if not price:
            return None
        return str(round(float(price), 2))

    def _extract_company(self, utt):
        rx_file = self.find_resource('company.rx', 'regex')
        LOG.debug(f"Resolved: {rx_file}")
        if rx_file:
            with open(rx_file) as f:
                for pat in f.read().splitlines():
                    pat = pat.strip()
                    if pat and pat[0] == "#":
                        continue
                    res = re.search(pat, utt)
                    if res:
                        try:
                            return res.group("Company")
                        except IndexError:
                            pass
        return None

    # Duplicated from OVOSSkill for backwards-compat with skills using ovos-workshop 0.X
    def _register_public_api(self):
        """
        Find and register API methods decorated with `@api_method` and create a
        messagebus handler for fetching the api info if any handlers exist.
        """

        def wrap_method(fn, arg_model=None):
            """Boilerplate for returning the response to the sender."""

            def wrapper(message):
                result = None
                error = None
                try:
                    if arg_model:
                        result = fn(arg_model(*message.data['args'], 
                                              **message.data['kwargs']))
                    else:
                        result = fn(*message.data.get('args', []), 
                                    **message.data.get('kwargs', {}))
                    try:
                        result = result.model_dump()
                    except AttributeError:
                        # Response is not a Pydantic model
                        pass
                except Exception as e:
                    error = str(e)
                message.context["skill_id"] = self.skill_id
                self.bus.emit(message.response(data={'result': result,
                                                     'error': error}))
            return wrapper

        from ovos_utils.skills import get_non_properties
        methods = [attr_name for attr_name in get_non_properties(self)
                   if hasattr(getattr(self, attr_name), '__name__')]

        for attr_name in methods:
            method = getattr(self, attr_name)

            if hasattr(method, 'api_method'):
                doc = method.__doc__ or ''
                name = method.__name__

                # Extract method signature and return type
                import inspect
                signature = inspect.signature(method)
                schema = None
                return_schema = None
                request_class = None
                try:
                    from pydantic import BaseModel
                    parameters = signature.parameters

                    for arg_name, param in parameters.items():
                        if arg_name == 'self':
                            continue
                        if issubclass(param.annotation, BaseModel):
                            # Get the JSON schema for the BaseModel
                            schema = param.annotation.model_json_schema()
                            request_class = param.annotation
                            break
                    if signature.return_annotation and issubclass(signature.return_annotation, BaseModel):
                        # Get the JSON schema for the return type
                        return_schema = signature.return_annotation.model_json_schema()
                except ImportError:
                    # If pydantic is not installed, there is no schema to extract
                    pass

                self.public_api[name] = {
                    'help': doc,
                    'type': f'{self.skill_id}.{name}',
                    'func': method,
                    'signature': str(signature),
                    'request_schema': schema,
                    'response_schema': return_schema,
                    'request_class': request_class
                }
        for key in self.public_api:
            if ('type' in self.public_api[key] and
                    'func' in self.public_api[key]):
                self.log.debug(f"Adding api method: "
                               f"{self.public_api[key]['type']}")

                # remove the function member since it shouldn't be
                # reused and can't be sent over the messagebus
                func = self.public_api[key].pop('func')
                req_class = self.public_api[key].pop('request_class', None)
                self.add_event(self.public_api[key]['type'],
                               wrap_method(func, req_class), speak_errors=False)

        if self.public_api:
            # TODO: Think about always registering this, so queries get an 
            #  empty response, rather than waiting for a timeout
            self.add_event(f'{self.skill_id}.public_api',
                           self._send_public_api, speak_errors=False)
