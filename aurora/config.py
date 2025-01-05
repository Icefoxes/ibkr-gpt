import logging
import os
from configparser import ConfigParser, NoSectionError, NoOptionError
from os import path

NOTIFICATION_SECTOR = 'notification'
OPENAI = 'chat'
TRADE = 'trade'


class TradeBotConf:
    def __init__(self, conf: ConfigParser = None) -> None:
        """
        Initialize the TradeBotConf with values from the configuration file.
        """
        try:
            self.notification_prefix = conf.get(NOTIFICATION_SECTOR, 'prefix')
            self.notification_period = conf.get(NOTIFICATION_SECTOR, 'period')
            self.notification_token = conf.get(NOTIFICATION_SECTOR, 'token')
        except (NoSectionError, NoOptionError):
            logging.warning('Notification configuration not found')
            self.notification_prefix = ''
            self.notification_period = ''
            self.notification_token = ''

        try:
            self.bot_key = conf.get(OPENAI, 'key')
            self.bot_model = conf.get(OPENAI, 'model')
            self.bot_url = conf.get(OPENAI, 'url')
        except (NoSectionError, NoOptionError):
            logging.warning('Chat configuration not found')
            self.bot_key = ''
            self.bot_model = ''
            self.bot_url = ''

        try:
            self.symbols = conf.get(TRADE, 'symbols')
        except (NoSectionError, NoOptionError):
            logging.warning('Trade configuration not found')
            self.symbols = ''

    @staticmethod
    def load() -> 'TradeBotConf':
        """
        Load the configuration from the 'app.conf' file.
        """
        parser = ConfigParser()
        root_dir = os.path.abspath(os.curdir)
        conf_file = path.join(root_dir, 'app.conf')
        if path.exists(conf_file):
            parser.read(conf_file, encoding='UTF-8')
            return TradeBotConf(parser)
        else:
            return TradeBotConf(ConfigParser())
