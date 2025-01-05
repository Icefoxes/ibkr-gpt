import datetime
import logging

import requests

from aurora.config import TradeBotConf


class Messenger:
    def __init__(self, conf: TradeBotConf) -> None:
        self.start, self.end = conf.notification_period.split('-')
        self.last_notify = None

    def _send_message(self, text: str) -> bool:
        """
        Args:
            text: text message
        Returns:
        """
        pass

    def notify(self, text: str) -> bool:
        now = datetime.datetime.now(datetime.UTC)
        if int(self.start) <= now.hour < int(self.end):
            return self._send_message(text)
        else:
            logging.info(f'message = {text} not sent')

    def notify_with_interval(self, text, minute: int = 5) -> bool:
        now = datetime.datetime.now(datetime.UTC)
        if not self.last_notify or (now - self.last_notify).seconds >= minute * 60:
            self.last_notify = now
            return self.notify(text)


class DingDingMessenger(Messenger):
    def __init__(self, conf: TradeBotConf) -> None:
        super().__init__(conf)

        self.prefix = conf.notification_prefix
        self.url = f'https://oapi.dingtalk.com/robot/send?access_token={conf.notification_token}'
        self.session = requests.session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def _send_message(self, text) -> bool:
        data = {
            'msgtype': 'text',
            'text': {
                'content': f'{self.prefix} {text}'
            }
        }
        response = self.session.post(self.url, json=data)
        return 'errmsg' in response.json() and response.json()['errmsg'] == 'ok'
