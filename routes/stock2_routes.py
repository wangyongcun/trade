import os
import pandas as pd
from flask import render_template

def register_stock2_routes(app):
    # 读取股票数据
    def read_stock_data(file_path):
        df = pd.read_excel(file_path)
        # 确保日期格式正确
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['trade_date'] = df['trade_date'].dt.strftime('%Y/%m/%d')
        # 按日期排序
        df = df.sort_values('trade_date')
        return df

    # 处理周K数据
    def process_weekly_data(stock_data):
        stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
        stock_data['week'] = stock_data['date'].dt.isocalendar().week
        stock_data['year'] = stock_data['date'].dt.isocalendar().year
        
        weekly_data = stock_data.groupby(['year', 'week']).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'trade_date': 'last'
        }).reset_index()
        
        return weekly_data

    # 处理月K数据
    def process_monthly_data(stock_data):
        stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
        stock_data['month'] = stock_data['date'].dt.month
        stock_data['year'] = stock_data['date'].dt.year
        
        monthly_data = stock_data.groupby(['year', 'month']).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'trade_date': 'last'
        }).reset_index()
        
        return monthly_data

    # 处理年K数据
    def process_yearly_data(stock_data):
        stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
        stock_data['year'] = stock_data['date'].dt.year
        
        yearly_data = stock_data.groupby('year').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'trade_date': 'last'
        }).reset_index()
        
        return yearly_data

    @app.route('/stock2/<code>')
    def stock2_chart(code):
        # 查找对应的股票文件
        stock_files = [f for f in os.listdir('stock-data') if f.startswith(code)]
        if not stock_files:
            return "股票代码不存在"
        
        file_path = os.path.join('stock-data', stock_files[0])
        stock_name = stock_files[0].split('_')[1].replace('.xlsx', '')
        
        # 读取原始数据
        original_data = read_stock_data(file_path)
        
        # 处理日K数据
        day_data = original_data.copy()
        day_dates = day_data['trade_date'].tolist()
        day_values = [[float(day_data.loc[i, 'open']), 
                       float(day_data.loc[i, 'close']), 
                       float(day_data.loc[i, 'low']), 
                       float(day_data.loc[i, 'high'])] 
                      for i in day_data.index]
        
        # 处理周K数据
        week_data = process_weekly_data(original_data.copy())
        week_dates = week_data['trade_date'].tolist()
        week_values = [[float(week_data.loc[i, 'open']), 
                        float(week_data.loc[i, 'close']), 
                        float(week_data.loc[i, 'low']), 
                        float(week_data.loc[i, 'high'])] 
                       for i in week_data.index]
        
        # 处理月K数据
        month_data = process_monthly_data(original_data.copy())
        month_dates = month_data['trade_date'].tolist()
        month_values = [[float(month_data.loc[i, 'open']), 
                         float(month_data.loc[i, 'close']), 
                         float(month_data.loc[i, 'low']), 
                         float(month_data.loc[i, 'high'])] 
                        for i in month_data.index]
        
        # 处理年K数据
        year_data = process_yearly_data(original_data.copy())
        year_dates = year_data['trade_date'].tolist()
        year_values = [[float(year_data.loc[i, 'open']), 
                        float(year_data.loc[i, 'close']), 
                        float(year_data.loc[i, 'low']), 
                        float(year_data.loc[i, 'high'])] 
                       for i in year_data.index]
        
        # 组织所有K线数据
        all_kline_data = {
            'day': {
                'dates': day_dates,
                'values': day_values
            },
            'week': {
                'dates': week_dates,
                'values': week_values
            },
            'month': {
                'dates': month_dates,
                'values': month_values
            },
            'year': {
                'dates': year_dates,
                'values': year_values
            }
        }
        
        return render_template('stock2.html', 
                               all_kline_data=all_kline_data, 
                               stock_name=stock_name)