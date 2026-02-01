import pandas_ta as ta

def add_rsi(df, length):
    df["rsi"] = ta.rsi(df["close"], length=length)
    return df
