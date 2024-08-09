from polygon import RESTClient
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression

# RSI = 100 - [100 / (1 + average up / average down)]
# Fetch historical stock data using Polygon
client = RESTClient("yqvFF3xXbbTJiAzHwPa3AaIEc5pxJfjo")
# client = RESTClient("YOUR_API_KEY")
aggs = client.get_aggs("AMZN", 1, "minute", "2023-01-16", "2023-01-20")
x_close = []
y_close = []
for i in range(0, len(aggs), 1):
  agg = aggs[i]
  x_close.append(datetime.fromtimestamp(agg.timestamp // 1000).strftime("%m/%d %H:%M"))
  y_close.append(agg.close)

print(x_close)
print(y_close)

plt.plot(x_close, y_close)
ax = plt.gca()
ax.set_xticks(ax.get_xticks()[::300])
plt.show()

class MovingAverage:
  def __init__(self, typ, period):
    self.period = period
    self.typ = typ
    self.data = []
    self.avg = -1 # needs updating - at least 1 day(s) of data required
  
  def update(self, new_delta):
    if self.typ == "gain" and new_delta < 0:
      new_delta = 0
    elif self.typ == "loss" and new_delta > 0:
      new_delta = 0
    self.data.append(abs(new_delta))
    if len(self.data) > self.period:
      self.data.pop(0)
    self.avg = sum(self.data) / len(self.data)
  

class RelativeStrengthIndex:
  def __init__(self, period=28):
    self.period = period
    self.last = -1
    self.gain_avg = MovingAverage("gain", period)
    self.loss_avg = MovingAverage("loss", period)
    self.rsi = -1 # needs updating - more than [period] day(s) of data required
    self.count = 0
  
  def update(self, new_data_point, time=""):
    if self.last >= 0:
      self.gain_avg.update(new_data_point - self.last)
      self.loss_avg.update(new_data_point - self.last)
    self.last = new_data_point
    self.count += 1
    if self.count > self.period:
      self.rsi = 100 - (100 / (1 + self.gain_avg.avg / self.loss_avg.avg))

data_x = []
data_y = []
low = []
high = []
rsi = RelativeStrengthIndex()
last_rsi = -1
buys = []
sells = []
for time, point in zip(x_close, y_close):
  rsi.update(point, time)
  if rsi.count > rsi.period:
    if last_rsi < 0:
      last_rsi = rsi.rsi
    data_x.append(time)
    data_y.append(rsi.rsi)
    low.append(30)
    high.append(70)
    if last_rsi < 30 and rsi.rsi >= 30:
      buys.append(time)
    if last_rsi > 70 and rsi.rsi <= 70:
      sells.append(time)
    last_rsi = rsi.rsi

y_close = y_close[len(y_close) - len(data_y):]

ndivs = []
pdivs = []
last = 0

window = 120
for i in range(window, len(y_close)):
  if i - last < window:
    continue
  x = np.array(range(0, window))
  y1 = np.array(y_close[i - window:i])
  y2 = np.array(data_y[i - window:i])
  model1 = LinearRegression()
  model1.fit(x.reshape(-1, 1), y1)
  model2 = LinearRegression()
  model2.fit(x.reshape(-1, 1), y2)
  trnd1 = model1.predict(x.reshape(-1, 1))
  trnd2 = model2.predict(x.reshape(-1, 1))
  slope1 = model1.coef_[0]
  slope2 = model2.coef_[0]
  if abs(slope1) < 0.004 or abs(slope2) < 0.04: # min reqs, because if slope is small, it's not a divergence
    continue
  if (slope1 > 0 and slope2 < 0) or (slope1 < 0 and slope2 > 0):
    # uncomment out if you want to show the divergences
    # plt.figure(figsize=(10, 6))
    # plt.plot(x, y1, label='Original Data')
    # plt.plot(x, trnd1, label='Trend Line', color='red')
    # plt.title('Price Direction using Linear Regression')
    # plt.xlabel('Index')
    # plt.ylabel('Value')
    # plt.legend()
    # plt.show()
    #
    # plt.figure(figsize=(10, 6))
    # plt.plot(x, y2, label='Original Data')
    # plt.plot(x, trnd2, label='Trend Line', color='red')
    # plt.title('RSI Direction using Linear Regression')
    # plt.xlabel('Index')
    # plt.ylabel('Value')
    # plt.legend()
    # plt.show()
    if slope1 > 0:
      ndivs.append(data_x[i])
    else:
      pdivs.append(data_x[i])
    # divs.append(data_x[i])
    last = i

plt.title("AMZN Stock Price RSI Indicator with Divergence")
plt.plot(data_x, data_y)
plt.plot(data_x, low)
plt.plot(data_x, high)
for buy in pdivs:
  plt.axvline(x=buy, color="green")
for sell in ndivs:
  plt.axvline(x=sell, color="red")
ax = plt.gca()
ax.set_xticks(ax.get_xticks()[::300])
plt.show()

plt.plot(data_x, y_close)
plt.title("AMZN Stock Price with Buy/Sell by RSI Divergence")
for buy in pdivs:
  plt.axvline(x=buy, color="green")
for sell in ndivs:
  plt.axvline(x=sell, color="red")
ax = plt.gca()
ax.set_xticks(ax.get_xticks()[::300])
plt.show()
