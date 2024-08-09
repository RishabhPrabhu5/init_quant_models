from polygon import RESTClient
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# Replace with your Polygon API key
API_KEY = 'cJOFUfv1fMrxfeArMfYhGjKvs4rA0IQi'

def fetch_data(symbol, multiplier, timespan, from_date, to_date):
    client = RESTClient(API_KEY)
    aggs = client.get_aggs(symbol, multiplier, timespan, from_date, to_date)
    
    timestamps = []
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []
    volumes = []
    
    for agg in aggs:
        timestamps.append(datetime.fromtimestamp(agg.timestamp // 1000))
        open_prices.append(agg.open)
        high_prices.append(agg.high)
        low_prices.append(agg.low)
        close_prices.append(agg.close)
        volumes.append(agg.volume)
        
    data = {
        't': timestamps,
        'o': open_prices,
        'h': high_prices,
        'l': low_prices,
        'c': close_prices,
        'v': volumes
    }
    
    df = pd.DataFrame(data)
    return df

def calculate_fibonacci_levels(first_hour_df):
    high = first_hour_df['h'].max()
    low = first_hour_df['l'].min()
    
    diff = high - low
    levels = {
        '0%': low,
        '23.6%': low + 0.236 * diff,
        '38.2%': low + 0.382 * diff,
        '50%': low + 0.5 * diff,
        '61.8%': low + 0.618 * diff,
        '100%': high
    }
    return levels

def identify_choch(df, window_size=2):
    choch = []
    for i in range(window_size, len(df)):
        avg_prev_close = df['c'].iloc[i-window_size:i].mean()
        if df['c'].iloc[i] > avg_prev_close and df['c'].iloc[i-1] <= avg_prev_close:
            choch.append('CHOCH Up')
        elif df['c'].iloc[i] < avg_prev_close and df['c'].iloc[i-1] >= avg_prev_close:
            choch.append('CHOCH Down')
        else:
            choch.append(None)
    df['CHOCH'] = [None] * window_size + choch
    return df

def generate_signals(df, levels):
    signals = []
    touched_level = None

    for i in range(len(df)):
        signal = 'Hold'
        if i < 13:
            signals.append(signal)
            continue
        
        for level_name, level_price in levels.items():
            if abs(df['c'].iloc[i] - level_price) < 0.01:
                touched_level = level_name
                break
        
        if touched_level in ['50%', '61.8%'] and df['CHOCH'].iloc[i] == 'CHOCH Up':
            signal = 'Buy'
        elif df['c'].iloc[i] < levels['50%'] and df['CHOCH'].iloc[i] == 'CHOCH Down':
            signal = 'Sell'
        elif touched_level in ['50%', '61.8%'] and df['CHOCH'].iloc[i] == 'CHOCH Down':
            signal = 'Sell'
        elif df['c'].iloc[i] > levels['50%'] and df['CHOCH'].iloc[i] == 'CHOCH Up':
            signal = 'Buy'
        
        signals.append(signal)
        if signal in ['Buy', 'Sell']:
            touched_level = None
    
    df['Signal'] = signals
    return df

def plot_signals(df, levels):
    fig, ax = plt.subplots(figsize=(14, 7))
    fib_colors = ['g', 'b', 'r', 'c', 'm', 'y']
    
    ax.plot(df['t'], df['c'], color='black', label='Close')
    buy_signals = df[df['Signal'] == 'Buy']
    sell_signals = df[df['Signal'] == 'Sell']
    ax.scatter(buy_signals['t'], buy_signals['c'], marker='^', s=100, color='green', label='Buy Signal')
    ax.scatter(sell_signals['t'], sell_signals['c'], marker='v', s=100, color='red', label='Sell Signal')
    
    for i, (level, price) in enumerate(levels.items()):
        color = fib_colors[i % len(fib_colors)]
        ax.hlines(price, xmin=df['t'].iloc[0], xmax=df['t'].iloc[-1], colors=color, linestyles='--', label=f'Fibonacci {level}')
    
    ax.set_title('Fibonacci Retracement Trading Signals with CHOCH')
    ax.set_ylabel('Price')
    ax.legend()
    
    plt.show()

def fib_choch_strategy(ticker, day, cash=100000, shares=1000, percent_invest=20):
    df_5min = fetch_data(ticker, 5, 'minute', day, day)
    first_hour_df = df_5min.iloc[:12]
    levels = calculate_fibonacci_levels(first_hour_df)
    df_5min = identify_choch(df_5min)
    df_5min = generate_signals(df_5min, levels)
    
    df_1min = fetch_data(ticker, 1, 'minute', day, day)
    transaction_times = df_5min[df_5min['Signal'].isin(['Buy', 'Sell'])][['t', 'Signal', 'c']].values.tolist()
    
    portfolio_val_s = cash + df_1min['c'].iloc[0] * shares
    amt = cash * percent_invest / 100

    for order in transaction_times:
        signal_time, signal, price = order
        next_time = signal_time + timedelta(minutes=1)
        
        if next_time not in df_1min['t'].values:
            continue
        
        next_price = df_1min.loc[df_1min['t'] == next_time, 'c'].values[0]

        if signal == 'Buy':
            cash -= amt
            shares += amt / next_price
        elif signal == 'Sell':
            cash += amt
            shares -= amt / next_price

    portfolio_val_e = cash + df_1min['c'].iloc[-1] * shares
    profit = portfolio_val_e - portfolio_val_s
    profit_percentage = (profit / portfolio_val_s) * 100
    
    # plot_signals(df_5min, levels)
    
    return [cash, shares, profit, profit_percentage]

print(fib_choch_strategy("NVDA", "2024-04-25", 100000, 1000, 20))
