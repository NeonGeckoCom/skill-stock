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

from pydantic import BaseModel, Field, model_validator


class StockPriceRequest(BaseModel):
    symbol: str = Field(description="Symbol to look up")


class StockPriceInfo(BaseModel):
    symbol: str = Field(description="Stock symbol")
    open: float = Field(description="Day opening price")
    high: float = Field(description="Day highest price")
    low: float = Field(description="Day lowest price")
    price: float = Field(description="Current price")
    volume: int = Field(description="Current share volume")
    latest_trading_day: str = Field(description="Date of latest trading day")
    previous_close: float = Field(description="Previous day closing price")
    change: float = Field(description="Change since previous close")
    change_percent: str = Field(description="Change percent since previous close")
    provider: str = Field(default="Alpha Vantage", description="Data provider")

    @model_validator(mode="before")
    def parse_global_quote(cls, data):
        if "Global Quote" in data:
            data = data["Global Quote"]
        new_data = {}
        for key, val in data.items():
            if len(key.split(". ")) > 1:
                new_data[key.split(". ")[1].replace(' ', '_')] = val
            else:
                # "Normal" response data, don't try to parse as AlphaVantage
                new_data[key] = val
        return new_data
