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

import unittest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from ovos_utils.messagebus import FakeBus
from mycroft_bus_client import Message
from mycroft.skills.skill_loader import SkillLoader


class TestSkill(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)

        # Override the configuration and fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs
        cls.skill._init_settings()
        cls.skill.initialize()

        # Override MQ config to use test endpoint
        cls.skill.config_core["MQ"] = {
            "server": "mq.2022.us",
            "port": 25672,
            "users": {
                "mq_handler": {
                    "user": "neon_api_utils",
                    "password": "Klatchat2021"
                }
            }
        }

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills.neon_skill import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)
        self.assertIsInstance(self.skill.translate_co, dict)
        self.assertIsInstance(self.skill.preferred_market, str)

        self.assertIsInstance(self.skill.service, str)
        self.assertIsNone(self.skill.api_key)
        self.assertTrue(hasattr(self.skill.data_source,
                                "search_stock_by_name"))
        self.assertTrue(hasattr(self.skill.data_source,
                                "get_stock_quote"))

    def test_handle_stock_price(self):
        message = Message("test", {"Company": "3m"})
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

        message = Message("test", {"Company": "microsoft"})
        self.skill.handle_stock_price(message)
        args = self.skill.speak_dialog.call_args
        self.assertEqual(args[0][0], "stock.price")
        data = args[1]["data"]
        self.assertEqual(data["symbol"], "MSFT")
        self.assertEqual(data["company"], "Microsoft Corporation")
        self.assertIsInstance(float(data["price"]), float)
        self.assertEqual(data["provider"], "Alpha Vantage")
        self.assertIsInstance(args[1]["data"], dict)

    def test_search_company(self):
        # TODO
        pass

    def test_get_stock_price(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
