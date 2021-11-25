import datetime
import yfinance as yf
import pandas as pd

stocks = ["AMZN", "MSFT", "FB", "GOOG"]

start = datetime.datetime.today() - datetime.timedelta(30)
end = datetime.datetime.today()
cl_price = pd.DataFrame()  # Empty dataframe that will be filled with closing prices
ohlcv_data = {}

for ticker in stocks:
    cl_price[ticker] = yf.download(ticker, start, end)["Adj Close"]

for ticker in stocks:
    temp = yf.download(ticker, period='1mo', interval='5m')
    temp.dropna(how='any', inplace=True)
    ohlcv_data[ticker] = temp

#Indicator
#Moving Average
def MACD(DF, a=12, b=26, c=9):
    df = DF.copy()
    df["ma_fast"] = df['Adj Close'].ewm(span=a, min_periods=a).mean()
    df["ma_slow"] = df['Adj Close'].ewm(span=b, min_periods=b).mean()
    df['macd'] = df['ma_fast'] - df['ma_slow']
    df['signal'] = df['macd'].ewm(span=c, min_periods=c).mean()
    return df.loc[:, ['macd', 'signal']]

for ticker in ohlcv_data:
    ohlcv_data[ticker][['MACD', "SIGNAL"]] = MACD(ohlcv_data[ticker])

#Performance Measure
def CAGR(DF):
    df = DF.copy()
    df["return"] = df["Adj Close"].pct_change()
    df["cum_return"] = (1+df["return"]).cumprod()
    n = len(df)/252 #252 is number of trading days in a year
    CAGR = (df["cum_return"][-1])**(1/n) - 1
    return CAGR

for ticker in ohlcv_data:
    print("CAGR for {} = {}".format(ticker, CAGR(ohlcv_data[ticker])))