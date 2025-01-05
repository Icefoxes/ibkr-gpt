import logging

from aurora.agent import TradingAgent
from aurora.config import TradeBotConf
from aurora.ibkr import IBApi

logging.basicConfig(filename='log.txt',
                    format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
                    level=logging.INFO)

__all__ = ['TradeBotConf', 'IBApi', 'TradingAgent']
