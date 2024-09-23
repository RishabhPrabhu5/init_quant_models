from polygon import RESTClient
from flask import Flask, request, jsonify
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import time
import os
import random

app = Flask(__name__)

# Function to simulate generating trade data, profit, and charts
def process_stock(ticker):
    # Mock trade data and profit calculation (replace with your logic)
    
    alphas_dict = {}
    profits_dict = {}   
    tickers = [ticker]
    # start_date = "2024-06-22"
    # end_date =  "2024-08-22"
    start_date = "2024-07-04"
    end_date =  "2024-09-04"
    initial_portfolio_value = 1000000
    count = 0

    for ticker in tickers:
        if count % 5 == 0 and count != 0:
            print("Waiting for 60 seconds to avoid rate limit")
            time.sleep(61)
        count += 1

    data = get_data(ticker, start_date, end_date)
    # replace start price with start price of stock (you can find it in yahoo finance)
    start_price = data[0].close

    initial_cash = 0.5 * initial_portfolio_value
    initial_shares = (0.5 * initial_portfolio_value/start_price) if start_price > 0 else 1000
    percent_invest = 5
    alpha, profit = test_model(ticker, data, start_date, end_date, initial_cash, initial_shares, percent_invest) # can only run for about 1.5 yrs
    profits_dict[ticker] = profit
    alphas_dict[ticker] = alpha
    
    
    
    total_profit = profit

    # Generate two plots and save them as images

    image1_path = f'static/chart1.png'
    image2_path = f'static/chart2.png'


    return total_profit, image1_path, image2_path

# API endpoint to handle user input (POST request)
@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    data = request.json
    ticker = data.get('ticker')

    # Process stock ticker
    profit, image1_path, image2_path = process_stock(ticker)

    response = {
        "profit": profit,
        "images": [image1_path, image2_path]
    }
    return jsonify(response)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)


#works best with constant markets. Does not perform well with bullish or bearish markets

class SimpleMovingAverage:
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
  def __init__(self, period=14):
    self.period = period
    self.last = -1
    self.rsi = -1 # needs updating - more than [period=14] day(s) of data required
    self.count = 0
    self.gain_avg = SimpleMovingAverage("gain", period)
    self.loss_avg = SimpleMovingAverage("loss", period)
  
  def update(self, new_data_point, time=""):
    if self.last >= 0:
      self.gain_avg.update(new_data_point - self.last)
      self.loss_avg.update(new_data_point - self.last)
    self.last = new_data_point
    self.count += 1
    if self.count > self.period:
      self.rsi = 100 - (100 / (1 + self.gain_avg.avg / (0.000000000000000000001 + self.loss_avg.avg)))

def generate_date_array(year):
    dates = []
    # Start from the first day of the given year
    current_date = datetime(year, 1, 1)
    # End on the last day of the given year
    end_date = datetime(year + 1, 1, 1)
    
    while current_date < end_date:
        # Format the date as "yyyy-mm-dd" and add it to the list
        date_string = current_date.strftime("%Y-%m-%d")
        dates.append(date_string)
        # Move to the next day
        current_date += timedelta(days=1)
    
    return dates

def graph_profits(data, type_of_profit):
    # Extract keys and values
    dates = list(data.keys())
    values = list(data.values())

    # Convert string dates to datetime objects
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]

    # Create a plot
    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker='o', linestyle='-', color='b')

    # Format the x-axis to show dates properly
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.DayLocator())

    # Label the axes
    plt.xlabel('Date')
    plt.ylabel(type_of_profit)
    plt.title(f'Model {type_of_profit} vs Holding Stock')

    # Rotate date labels for better readability
    plt.xticks(rotation=45)

    # Show grid
    plt.grid(True)

    # Display the plot
    plt.tight_layout()
    plt.show()
    
    image2_path = f'static/chart2.png'
    plt.savefig(image2_path)


def graph_transactions(transactions):
  # Convert transactions to a DataFrame for easier manipulation
  df = pd.DataFrame(transactions, columns=['Date', 'Price', 'Type'])

  # Convert the 'Date' column to datetime objects
  df['Date'] = pd.to_datetime(df['Date'])

  # Separate the transactions by type
  sell_transactions = df[df['Type'] == 'Sell']
  buy_transactions = df[df['Type'] == 'Buy']

  # Plotting
  plt.figure(figsize=(10, 6))

  # Plot sell transactions in red
  plt.scatter(sell_transactions['Date'], sell_transactions['Price'], color='red', label='Sell', marker='x')

  # Plot buy transactions in green
  plt.scatter(buy_transactions['Date'], buy_transactions['Price'], color='green', label='Buy', marker='o')

  # Labels and title
  plt.xlabel('Date')
  plt.ylabel('Price')
  plt.title('Transaction Prices Over Time')
  plt.legend()

  # Format the date on the x-axis
  plt.gcf().autofmt_xdate()
  
  
  
  image1_path = f'static/chart1.png'
  plt.savefig(image1_path)

  # Show the plot
  plt.show()
  
  

def get_data(ticker, start_date, end_date):
    client = RESTClient("InxdvvQ5aFMwk5xWUpJUCpe8YHcimh8d")
    aggs = client.get_aggs(ticker, 1, "hour", start_date, end_date, limit=50000)
    print("Number of Data Points:",len(aggs))
    return aggs
    
    
def run_simulation(ticker, start_date, end_date, init_cash, init_shares, percent_invest, prices, times, buys, sells):
  transaction_times = sorted(buys + sells)
  transactions = []
  for t in transaction_times:
    price = prices[times.index(t)]
    if t in buys:
      transactions.append([t, price, "Buy"])
    else:
      transactions.append([t, price, "Sell"])
      
  print("Transactions: ", transactions)
  graph_transactions(transactions)
  # Execute Transactions through simulation
  cash = init_cash
  shares = init_shares
  print("Running Simulation for RSI with", ticker, "from", start_date, "to", end_date)
  print("Number of Transactions: ", len(transactions))
  print("Buys: ", len(buys), "Sells: ", len(sells))
  print("Open Price, Close Price: ", prices[0], prices[-1])
  print("Beginning Cash and Shares: ", cash, shares)
  portfolio_val_s = cash + prices[0] * shares
  print("Beginning Portfolio Value: ", portfolio_val_s)
  amt = cash * percent_invest / 100
  for order in transactions:
    if order[2] == "Buy":
      cash -= amt
      shares += amt/order[1]
    else:
      cash += amt
      shares -= amt/order[1]
  print("End Cash and Shares: ", cash, shares)
  portfolio_val_e = cash + prices[-1] * shares
  profit = portfolio_val_e - portfolio_val_s
  profit_percentage = (portfolio_val_e - portfolio_val_s) / portfolio_val_s * 100

  base_profit_percentage = init_shares*(prices[-1]-prices[0])/portfolio_val_s * 100

  print("End Portfolio Value: ", portfolio_val_e)
  print()
  print("Model Profit Percentage: ", profit_percentage)
  print("Market Change w/o trades", base_profit_percentage)
  print()
  print("Model outperforms market by", (profit_percentage - base_profit_percentage), "%") 


  return [cash, shares, profit, profit_percentage, base_profit_percentage]
def invest_rsi(ticker, data, start_date, end_date, cash=100000, shares=1000, percent_invest=20):
  aggs = data
  x_close = []
  y_close = []
  min_diff = 1
  for i in range(0, len(aggs), min_diff):
    agg = aggs[i]
    x_close.append(datetime.fromtimestamp(agg.timestamp // 1000).strftime("%Y-%m-%d %H:%M"))
    y_close.append(agg.close)

  
  #check if there is data for this time period
  if len(y_close) == 0:
    print("no data for this time period and stock")
    return(cash, shares, 0, 0, 0)

  # RSI execution
  data_x = []
  data_y = []
  low = []
  high = []
  rsi = RelativeStrengthIndex()
  last_rsi = -1
  buys = []
  sells = []
  
  # Parameters for trade strategy/execution
  low_threshold = 25
  high_threshold = 75
  
  for time, point in zip(x_close, y_close):
    rsi.update(point, time)
    if rsi.count > rsi.period:
      if last_rsi < 0:
        last_rsi = rsi.rsi
      data_x.append(time)
      data_y.append(rsi.rsi)
      low.append(low_threshold)
      high.append(high_threshold)
      if last_rsi < low_threshold and rsi.rsi >= low_threshold:
        buys.append(time)
      if last_rsi > high_threshold and rsi.rsi <= high_threshold:
        sells.append(time)
      last_rsi = rsi.rsi
      
  plt.figure(figsize=(10, 4))    
  plt.title(ticker + " RSI Indicator with Signals")
  plt.plot(data_x, data_y)
  plt.plot(data_x, low)
  plt.plot(data_x, high)
  for buy in buys:
    plt.axvline(x=buy, color="green")
  for sell in sells:
    plt.axvline(x=sell, color="red")
  ax = plt.gca()
  ax.set_xticks(ax.get_xticks()[::30])
  plt.show()

  plt.figure(figsize=(10, 4))
  plt.plot(x_close, y_close)
  plt.title(ticker + " Stock Price with Buy/Sell by RSI Indicator")
  for buy in buys:
    plt.axvline(x=buy, color="green")
  for sell in sells:
    plt.axvline(x=sell, color="red")
  ax = plt.gca()
  ax.set_xticks(ax.get_xticks()[::30])
  plt.show()

  return run_simulation(ticker, start_date, end_date, cash, shares, percent_invest, y_close, x_close, buys, sells)

def test_model(ticker, data, start_date, end_date, init_cash, init_shares, percent_invest):
    year1 = int(start_date[:4])
    year2 = int(end_date[:4])
    date_array = []
    for year in range(year1, year2+1):
        date_array += generate_date_array(year)

    
    cash, shares, profit, profit_percentage, base_profit_percentage = invest_rsi(ticker, data, start_date, end_date, init_cash, init_shares, percent_invest)
    alpha = profit_percentage - base_profit_percentage

    return alpha, profit_percentage

