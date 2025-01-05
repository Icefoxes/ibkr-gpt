import logging
from openai import OpenAI, OpenAIError

from aurora.config import TradeBotConf
from aurora.models import AuroraAdvise, AuroraDecisionRequest


class TradingAgent:
    def __init__(self, conf: TradeBotConf, prompt: str):
        self.model = conf.bot_model
        self.client = OpenAI(
            api_key=conf.bot_key,
            base_url=conf.bot_url
        )
        self.messages = [
            {'role': 'system', 'content': prompt}
        ]

    def ask(self, message: AuroraDecisionRequest) -> AuroraAdvise:
        self.messages.append({'role': 'user', 'content': message.model_dump_json()})
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                store=True,
                stream=False,
                messages=self.messages
            )
            if len(completion.choices) > 0:
                choice = completion.choices[0]
                return AuroraAdvise.model_validate_json(json_data=choice.message.content)
        except OpenAIError as e:
            logging.error(f"OpenAI error: {e}")
