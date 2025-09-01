import os
import pandas as pd
from flask import render_template
from pyecharts import options as opts
from pyecharts.charts import Kline, Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from db_utils import read_stock_data as db_read_stock_data, get_stock_name

def register_stock_routes(app):
    # 读取股票数据
    def read_stock_data(file_path):
        df = pd.read_excel(file_path)
        # 确保日期格式正确
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['trade_date'] = df['trade_date'].dt.strftime('%Y/%m/%d')
        # 按日期排序
        df = df.sort_values('trade_date')
        return df

    # 生成K线图
    def generate_kline_chart(stock_data, stock_name):
        # 准备K线数据
        dates = stock_data['trade_date'].tolist()
        k_data = [[float(stock_data.loc[i, 'open']), 
                   float(stock_data.loc[i, 'close']), 
                   float(stock_data.loc[i, 'low']), 
                   float(stock_data.loc[i, 'high'])] 
                  for i in stock_data.index]
        
        # 计算移动平均线
        ma5_data = stock_data['close'].rolling(5).mean().tolist()
        ma10_data = stock_data['close'].rolling(10).mean().tolist()
        ma20_data = stock_data['close'].rolling(20).mean().tolist()
        ma30_data = stock_data['close'].rolling(30).mean().tolist()
        
        # 创建K线图
        kline = (
            Kline(init_opts=opts.InitOpts(width="1200px", height="600px", theme=ThemeType.WHITE))
            .add_xaxis(dates)
            .add_yaxis(
                "K线",
                k_data,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#14b143",
                    border_color="#ef232a",
                    border_color0="#14b143",
                    opacity=0.9
                ),
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最大值"),
                        opts.MarkPointItem(type_="min", name="最小值"),
                    ]
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{stock_name} - K线图"),
                xaxis_opts=opts.AxisOpts(is_scale=True),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1))
                ),
                datazoom_opts=[opts.DataZoomOpts(range_start=50, range_end=100)],
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                legend_opts=opts.LegendOpts(is_show=True, pos_top="top"),
                toolbox_opts=opts.ToolboxOpts(is_show=True)
            )
        )
        
        # 创建移动平均线
        line = (
            Line()
            .add_xaxis(dates)
            .add_yaxis("MA5", ma5_data, is_smooth=True, linestyle_opts=opts.LineStyleOpts(opacity=0.8))
            .add_yaxis("MA10", ma10_data, is_smooth=True, linestyle_opts=opts.LineStyleOpts(opacity=0.8))
            .add_yaxis("MA20", ma20_data, is_smooth=True, linestyle_opts=opts.LineStyleOpts(opacity=0.8))
            .add_yaxis("MA30", ma30_data, is_smooth=True, linestyle_opts=opts.LineStyleOpts(opacity=0.8))
        )
        
        # 将K线图和移动平均线叠加
        kline.overlap(line)
        return kline

    @app.route('/stock/<code>')
    def stock_chart(code):
        # 查找对应的股票文件
        stock_files = [f for f in os.listdir('stock-data') if f.startswith(code)]
        if not stock_files:
            return "股票代码不存在"
        
        file_path = os.path.join('stock-data', stock_files[0])
        stock_name = stock_files[0].split('_')[1].replace('.xlsx', '')
        
        # 读取数据并生成图表
        stock_data = read_stock_data(file_path)
        chart = generate_kline_chart(stock_data, stock_name)
        
        return render_template('stock.html', chart=chart.render_embed(), stock_name=stock_name)