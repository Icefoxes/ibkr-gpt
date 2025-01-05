from typing import List
import talib
import pandas as pd

from aurora.models import AuroraBar


def convert_to_datetime_with_tz(date_str):
    datetime_part, tz_part = date_str.rsplit(' ', 1)
    dt = pd.to_datetime(datetime_part, format='%Y%m%d %H:%M:%S')
    return dt.tz_localize(tz_part)

def round_value(value):
    if value == 0:
        return 0
    elif abs(value) < 1:
        return round(value, 7)
    else:
        return round(value, 3)
    
class IndicatorAnalyzer:
    def __init__(self):
        pass

    def analyze(self, bars: List[AuroraBar]):
        df = pd.DataFrame([bar.model_dump() for bar in bars])
        if df.empty:
            return ''
        df.date = df.date.apply(convert_to_datetime_with_tz)

        # Calculate moving averages
        df['MA5'] = talib.SMA(df['close'], timeperiod=5).apply(round_value)
        df['MA10'] = talib.SMA(df['close'], timeperiod=10).apply(round_value)
        df['MA20'] = talib.SMA(df['close'], timeperiod=20).apply(round_value)
        df['MA50'] = talib.SMA(df['close'], timeperiod=50).apply(round_value)

        # Calculate MACD
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['MACD'] = df['MACD'].apply(round_value)
        df['MACD_signal'] = df['MACD_signal'].apply(round_value)
        df['MACD_hist'] = df['MACD_hist'].apply(round_value)

        # Calculate Bollinger Bands
        df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        df['upper_band'] = df['upper_band'].apply(round_value)
        df['middle_band'] = df['middle_band'].apply(round_value)
        df['lower_band'] = df['lower_band'].apply(round_value)
        return df.to_csv(index=False, path_or_buf=None)
