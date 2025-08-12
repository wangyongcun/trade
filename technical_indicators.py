import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    """
    计算RSI指标
    :param prices: 收盘价序列
    :param period: 计算周期，默认14
    :return: RSI值序列
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """
    计算MACD指标
    :param prices: 收盘价序列
    :param fast_period: 快线周期，默认12
    :param slow_period: 慢线周期，默认26
    :param signal_period: 信号线周期，默认9
    :return: 包含MACD、Signal、Histogram的字典
    """
    ema_fast = prices.ewm(span=fast_period).mean()
    ema_slow = prices.ewm(span=slow_period).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    
    return {
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': histogram
    }

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    计算布林带指标
    :param prices: 收盘价序列
    :param period: 计算周期，默认20
    :param std_dev: 标准差倍数，默认2
    :return: 包含上轨、中轨、下轨的字典
    """
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return {
        'Upper': upper_band,
        'Middle': sma,
        'Lower': lower_band
    }

def calculate_kdj(high, low, close, period=9, k_period=3, d_period=3):
    """
    计算KDJ指标
    :param high: 最高价序列
    :param low: 最低价序列
    :param close: 收盘价序列
    :param period: RSV计算周期，默认9
    :param k_period: K值平滑周期，默认3
    :param d_period: D值平滑周期，默认3
    :return: 包含K、D、J值的字典
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    
    k = rsv.ewm(alpha=1/k_period).mean()
    d = k.ewm(alpha=1/d_period).mean()
    j = 3 * k - 2 * d
    
    return {
        'K': k,
        'D': d,
        'J': j
    }

def calculate_moving_averages(prices):
    """
    计算多种移动平均线
    :param prices: 收盘价序列
    :return: 包含不同周期MA的字典
    """
    return {
        'MA5': prices.rolling(5).mean(),
        'MA10': prices.rolling(10).mean(),
        'MA20': prices.rolling(20).mean(),
        'MA30': prices.rolling(30).mean(),
        'MA60': prices.rolling(60).mean()
    }

def process_stock_data_with_indicators(stock_data):
    """
    为股票数据添加技术指标
    :param stock_data: 原始股票数据DataFrame
    :return: 包含技术指标的DataFrame
    """
    data = stock_data.copy()
    
    # 确保数据类型正确
    data['close'] = pd.to_numeric(data['close'])
    data['high'] = pd.to_numeric(data['high'])
    data['low'] = pd.to_numeric(data['low'])
    data['open'] = pd.to_numeric(data['open'])
    
    # 添加成交量列（如果不存在）
    if 'vol' not in data.columns:
        # 模拟成交量数据（实际项目中应该有真实数据）
        np.random.seed(42)  # 保证可重现
        data['vol'] = np.random.randint(1000000, 10000000, len(data))
    
    # 计算移动平均线
    ma_data = calculate_moving_averages(data['close'])
    for key, value in ma_data.items():
        data[key] = value
    
    # 计算RSI
    data['RSI'] = calculate_rsi(data['close'])
    
    # 计算MACD
    macd_data = calculate_macd(data['close'])
    data['MACD'] = macd_data['MACD']
    data['MACD_Signal'] = macd_data['Signal']
    data['MACD_Histogram'] = macd_data['Histogram']
    
    # 计算布林带
    bb_data = calculate_bollinger_bands(data['close'])
    data['BB_Upper'] = bb_data['Upper']
    data['BB_Middle'] = bb_data['Middle']
    data['BB_Lower'] = bb_data['Lower']
    
    # 计算KDJ
    kdj_data = calculate_kdj(data['high'], data['low'], data['close'])
    data['KDJ_K'] = kdj_data['K']
    data['KDJ_D'] = kdj_data['D']
    data['KDJ_J'] = kdj_data['J']
    
    return data

def process_weekly_data_with_volume(stock_data):
    """
    处理周K数据（包含成交量处理）
    """
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    stock_data['week'] = stock_data['date'].dt.isocalendar().week
    stock_data['year'] = stock_data['date'].dt.isocalendar().year
    
    # 按年和周分组，计算周K数据
    weekly_data = stock_data.groupby(['year', 'week']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last',
        'vol': 'sum' if 'vol' in stock_data.columns else lambda x: 0  # 成交量求和
    }).reset_index()
    
    return weekly_data

def process_monthly_data_with_volume(stock_data):
    """
    处理月K数据（包含成交量处理）
    """
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    stock_data['month'] = stock_data['date'].dt.month
    stock_data['year'] = stock_data['date'].dt.year
    
    # 按年和月分组，计算月K数据
    monthly_data = stock_data.groupby(['year', 'month']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last',
        'vol': 'sum' if 'vol' in stock_data.columns else lambda x: 0  # 成交量求和
    }).reset_index()
    
    return monthly_data

def process_yearly_data_with_volume(stock_data):
    """
    处理年K数据（包含成交量处理）
    """
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    stock_data['year'] = stock_data['date'].dt.year
    
    # 按年分组，计算年K数据
    yearly_data = stock_data.groupby('year').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last',
        'vol': 'sum' if 'vol' in stock_data.columns else lambda x: 0  # 成交量求和
    }).reset_index()
    
    return yearly_data

def read_stock_data_enhanced(file_path):
    """
    增强版股票数据读取函数
    """
    df = pd.read_excel(file_path)
    # 确保日期格式正确
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    df['trade_date'] = df['trade_date'].dt.strftime('%Y/%m/%d')
    
    # 添加成交量列（如果不存在）
    if 'vol' not in df.columns:
        # 模拟成交量数据（实际项目中应该有真实数据）
        np.random.seed(42)  # 保证可重现
        df['vol'] = np.random.randint(1000000, 10000000, len(df))
    
    # 按日期排序
    df = df.sort_values('trade_date')
    return df