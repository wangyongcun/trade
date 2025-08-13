import os
import pandas as pd
from flask import render_template
from technical_indicators import (
    read_stock_data_enhanced, 
    process_stock_data_with_indicators,
    process_weekly_data_with_volume,
    process_monthly_data_with_volume,
    process_yearly_data_with_volume
)

def register_stock3_routes(app):
    # 读取股票数据
    def read_stock_data(file_path):
        df = pd.read_excel(file_path)
        # 确保日期格式正确
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['trade_date'] = df['trade_date'].dt.strftime('%Y/%m/%d')
        # 按日期排序
        df = df.sort_values('trade_date')
        return df

    @app.route('/stock3/<code>')
    def stock3_chart(code):
        # 查找对应的股票文件
        stock_files = [f for f in os.listdir('stock-data') if f.startswith(code)]
        if not stock_files:
            return "股票代码不存在"
        
        file_path = os.path.join('stock-data', stock_files[0])
        stock_name = stock_files[0].split('_')[1].replace('.xlsx', '')
        
        # 读取并处理原始数据
        original_data = read_stock_data_enhanced(file_path)
        
        # 处理日K数据并添加技术指标
        day_data = process_stock_data_with_indicators(original_data.copy())
        day_dates = day_data['trade_date'].tolist()
        day_values = [[float(day_data.loc[i, 'open']), 
                       float(day_data.loc[i, 'close']), 
                       float(day_data.loc[i, 'low']), 
                       float(day_data.loc[i, 'high'])] 
                      for i in day_data.index]
        
        # 处理周K数据
        week_raw = process_weekly_data_with_volume(original_data.copy())
        week_data = process_stock_data_with_indicators(week_raw)
        week_dates = week_data['trade_date'].tolist()
        week_values = [[float(week_data.loc[i, 'open']), 
                        float(week_data.loc[i, 'close']), 
                        float(week_data.loc[i, 'low']), 
                        float(week_data.loc[i, 'high'])] 
                       for i in week_data.index]
        
        # 处理月K数据
        month_raw = process_monthly_data_with_volume(original_data.copy())
        month_data = process_stock_data_with_indicators(month_raw)
        month_dates = month_data['trade_date'].tolist()
        month_values = [[float(month_data.loc[i, 'open']), 
                         float(month_data.loc[i, 'close']), 
                         float(month_data.loc[i, 'low']), 
                         float(month_data.loc[i, 'high'])] 
                        for i in month_data.index]
        
        # 处理年K数据
        year_raw = process_yearly_data_with_volume(original_data.copy())
        year_data = process_stock_data_with_indicators(year_raw)
        year_dates = year_data['trade_date'].tolist()
        year_values = [[float(year_data.loc[i, 'open']), 
                        float(year_data.loc[i, 'close']), 
                        float(year_data.loc[i, 'low']), 
                        float(year_data.loc[i, 'high'])] 
                       for i in year_data.index]
        
        # 准备所有技术指标数据
        def prepare_indicators_data(data):
            return {
                'vol': data['vol'].fillna(0).tolist(),
                'ma5': data['MA5'].fillna(0).tolist(),
                'ma10': data['MA10'].fillna(0).tolist(),
                'ma20': data['MA20'].fillna(0).tolist(),
                'ma30': data['MA30'].fillna(0).tolist(),
                'rsi': data['RSI'].fillna(50).tolist(),
                'macd': data['MACD'].fillna(0).tolist(),
                'macd_signal': data['MACD_Signal'].fillna(0).tolist(),
                'macd_histogram': data['MACD_Histogram'].fillna(0).tolist(),
                'bb_upper': data['BB_Upper'].fillna(0).tolist(),
                'bb_middle': data['BB_Middle'].fillna(0).tolist(),
                'bb_lower': data['BB_Lower'].fillna(0).tolist(),
                'kdj_k': data['KDJ_K'].fillna(50).tolist(),
                'kdj_d': data['KDJ_D'].fillna(50).tolist(),
                'kdj_j': data['KDJ_J'].fillna(50).tolist()
            }
        
        # 组织所有K线数据和技术指标
        all_kline_data = {
            'day': {
                'dates': day_dates,
                'values': day_values,
                'indicators': prepare_indicators_data(day_data)
            },
            'week': {
                'dates': week_dates,
                'values': week_values,
                'indicators': prepare_indicators_data(week_data)
            },
            'month': {
                'dates': month_dates,
                'values': month_values,
                'indicators': prepare_indicators_data(month_data)
            },
            'year': {
                'dates': year_dates,
                'values': year_values,
                'indicators': prepare_indicators_data(year_data)
            }
        }
        
        return render_template('stock3.html', 
                               all_kline_data=all_kline_data, 
                               stock_name=stock_name)