### IBKR-GPT
This project aims to combine the power of ChatGPT, a leading language model, with Interactive Brokers (IBKR) for automated trading. 
Leveraging ChatGPT's advanced natural language processing capabilities, we seek to enhance the trading decision-making process. 
It can analyze indicator. The integration with IBKR's trading API allows for seamless execution of trades based on the suggestions 
generated by ChatGPT. Traders can automate routine trading tasks, respond quickly to market changes, and potentially improve trading 
efficiency and profitability. Through this project, we strive to bridge the gap between cutting-edge artificial intelligence technology 
and the practical world of financial trading, offering a novel solution for both individual and institutional traders alike. 
Whether you're a seasoned trader looking to optimize your strategies or a novice exploring the possibilities of automated trading, 
this project has something to offer. Join us in this exciting journey of innovation in the financial technology space.
``
## Install with Python12 on Windows

### setup venv
```shell
python -m venv runtime
 .\runtime\Scripts\activate
```

### install ibkr
```commandline
cd libs/ikbr
pip install .
```

### install talib
```shell
cd libs/talib
pip install ta_lib-0.5.1-cp312-cp312-win_amd64.whl
```

### install other dept
```shell
pip install -r requirement.txt
```

2. setup environment
```editorconfig
[chat]
key =
url =
model =

[notification]
prefix = Alert
period = 1-15
token =

[trade]
symbols=IBKR
```

3. start application
```shell
python main.py
```