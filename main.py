import logging

from aurora import TradeBotConf, IBApi, TradingAgent

if __name__ == '__main__':
    logging.info('[1] init conf')
    conf = TradeBotConf.load()

    logging.info('[2] start agent')
    with open('./prompt.md', 'r') as f:
        prompt = f.read()
        agent = TradingAgent(conf, prompt)

        logging.info('[3] start server')
        app = IBApi(conf, agent)

        app.connect("127.0.0.1", 7497, 0)
        app.run()

