from polygon import RESTClient
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# get data
stock_symbol = "AMZN"  # Replace with your desired stock symbol
client = RESTClient("sOdQWQgI2Zs3yEUZSlBJObKba52LLMPg")  # Replace with your Polygon API key
aggs = client.get_aggs(stock_symbol, 1, "minute", "2024-03-25", "2024-03-25")

# prepare data
timestamps = []
close_prices = []
for agg in aggs:
    timestamps.append(datetime.fromtimestamp(agg.timestamp // 1000))
    close_prices.append(agg.close)

close_prices = np.array(close_prices)

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_macd(data):
    ema_12 = calculate_ema(data, 12)
    ema_26 = calculate_ema(data, 26)
    macd_line = ema_12 - ema_26
    signal_line = calculate_ema(macd_line, 9)
    return macd_line, signal_line

close_series = pd.Series(close_prices)
macd_line, signal_line = calculate_macd(close_series)

plt.figure(figsize=(14, 7))
plt.plot(timestamps, close_prices, label='Close Prices')
plt.title('Closing Prices')
plt.legend()
plt.show()

# plot MACD and Signal line with crossovers
plt.figure(figsize=(14, 7))
plt.plot(timestamps, macd_line, label='MACD Line', color='blue')
plt.plot(timestamps, signal_line, label='Signal Line', color='red')

# highlight crossovers
for i in range(1, len(macd_line)):
    if (macd_line[i-1] < signal_line[i-1]) and (macd_line[i] > signal_line[i]):
        plt.axvline(x=timestamps[i], color='red', linestyle='--', linewidth=0.5)  # Bullish crossover
    elif (macd_line[i-1] > signal_line[i-1]) and (macd_line[i] < signal_line[i]):
        plt.axvline(x=timestamps[i], color='green', linestyle='--', linewidth=0.5)  # Bearish crossover

plt.title('MACD and Signal Line with Crossovers')
plt.legend()
plt.show()