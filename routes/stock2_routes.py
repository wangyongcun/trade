import os
import pandas as pd
from flask import render_template

def register_stock2_routes(app):
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
        # 由 Excel 切换为从数据库读取，并从数据库获取股票名称
        from db_utils import read_stock_data as db_read_stock_data, get_stock_name
        stock_name = get_stock_name(code) or code
        original_data = db_read_stock_data(code)
        if original_data is None or original_data.empty:
            return "数据库中未找到该股票数据"
        
        # 处理日K数据
        day_data = original_data.copy()
        day_dates = day_data['trade_date'].tolist()
        day_values = [[float(day_data.loc[i, 'open']),
                       float(day_data.loc[i, 'close']),
                       float(day_data.loc[i, 'low']),
                       float(day_data.loc[i, 'high'])]
                      for i in day_data.index]
        
        # 处理周K、月K、年K（复用你原有的分组逻辑）
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
            'day': {'dates': day_dates, 'values': day_values},
            'week': {'dates': week_dates, 'values': week_values},
            'month': {'dates': month_dates, 'values': month_values},
            'year': {'dates': year_dates, 'values': year_values}
        }

        return render_template('stock2.html',
                               all_kline_data=all_kline_data,
                               stock_name=stock_name)