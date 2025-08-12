import os
import pandas as pd
from flask import Flask, render_template
from pyecharts import options as opts
from pyecharts.charts import Kline, Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from technical_indicators import (
    read_stock_data_enhanced, 
    process_stock_data_with_indicators,
    process_weekly_data_with_volume,
    process_monthly_data_with_volume,
    process_yearly_data_with_volume
)

app = Flask(__name__)

# 创建templates目录
os.makedirs('templates', exist_ok=True)

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
    # 将日期转换回datetime格式以便处理
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    # 添加周数信息
    stock_data['week'] = stock_data['date'].dt.isocalendar().week
    stock_data['year'] = stock_data['date'].dt.isocalendar().year
    
    # 按年和周分组，计算周K数据
    weekly_data = stock_data.groupby(['year', 'week']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last'  # 使用每周最后一天的日期
    }).reset_index()
    
    return weekly_data

# 处理月K数据
def process_monthly_data(stock_data):
    # 将日期转换回datetime格式以便处理
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    # 添加月份信息
    stock_data['month'] = stock_data['date'].dt.month
    stock_data['year'] = stock_data['date'].dt.year
    
    # 按年和月分组，计算月K数据
    monthly_data = stock_data.groupby(['year', 'month']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last'  # 使用每月最后一天的日期
    }).reset_index()
    
    return monthly_data

# 处理年K数据
def process_yearly_data(stock_data):
    # 将日期转换回datetime格式以便处理
    stock_data['date'] = pd.to_datetime(stock_data['trade_date'])
    # 添加年份信息
    stock_data['year'] = stock_data['date'].dt.year
    
    # 按年分组，计算年K数据
    yearly_data = stock_data.groupby('year').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'trade_date': 'last'  # 使用每年最后一天的日期
    }).reset_index()
    
    return yearly_data

# 生成K线图
def generate_kline_chart(stock_data, stock_name):
    # 准备数据
    dates = stock_data['trade_date'].tolist()
    k_data = [[float(stock_data.loc[i, 'open']), 
               float(stock_data.loc[i, 'close']), 
               float(stock_data.loc[i, 'low']), 
               float(stock_data.loc[i, 'high'])] 
              for i in stock_data.index]
    
    # 计算移动平均线数据
    stock_data['MA5'] = stock_data['close'].rolling(5).mean()
    stock_data['MA10'] = stock_data['close'].rolling(10).mean()
    stock_data['MA20'] = stock_data['close'].rolling(20).mean()
    stock_data['MA30'] = stock_data['close'].rolling(30).mean()
    
    # 找出最高点和最低点，用于添加标记
    max_price_idx = stock_data['high'].idxmax()
    min_price_idx = stock_data['low'].idxmin()
    max_price = stock_data.loc[max_price_idx, 'high']
    min_price = stock_data.loc[min_price_idx, 'low']
    max_date = stock_data.loc[max_price_idx, 'trade_date']
    min_date = stock_data.loc[min_price_idx, 'trade_date']
    
    # 找出其他重要点位（可以根据实际数据调整）
    # 这里模拟图中的2300点和2242点
    mid_points = [
        {"value": 2334, "date_idx": int(len(dates) * 0.8), "color": "#ef232a"},
        {"value": 2300, "date_idx": int(len(dates) * 0.85), "color": "#1d3f6b"},
        {"value": 2242, "date_idx": int(len(dates) * 0.5), "color": "#ef232a"},
        {"value": 2126, "date_idx": int(len(dates) * 0.95), "color": "#ef232a"}
    ]
    
    # 水平参考线
    upper_reference_line = 2324.02
    lower_reference_line = 2148.35
    
    # 创建K线图
    kline = (
        Kline(init_opts=opts.InitOpts(width="1200px", height="600px", theme=ThemeType.WHITE, bg_color="#ffffff"))
        .add_xaxis(dates)
        .add_yaxis(
            "日K",
            k_data,
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ef232a",
                color0="#14b143",
                border_color="#ef232a",
                border_color0="#14b143",
            ),
            markarea_opts=opts.MarkAreaOpts(
                data=[
                    # 标记背景区域，可以标记不同的时间段
                    [opts.MarkAreaItem(name="区间", x=dates[0]), opts.MarkAreaItem(x=dates[int(len(dates)*0.2)])],
                ],
                itemstyle_opts=opts.ItemStyleOpts(opacity=0.2),
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="上证指数",
                subtitle=stock_name,
                pos_left="left",
                title_textstyle_opts=opts.TextStyleOpts(color="#000", font_size=18, font_weight="bold"),
                subtitle_textstyle_opts=opts.TextStyleOpts(color="#666", font_size=14)
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(color="#eeeeee")),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
                axislabel_opts=opts.LabelOpts(rotate=0, font_size=10, color="#666666")
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(
                    is_show=True,
                    linestyle_opts=opts.LineStyleOpts(color="#eeeeee", width=1, type_="solid", opacity=0.8)
                ),
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=0.05)
                ),
                axislabel_opts=opts.LabelOpts(font_size=10, color="#666666")
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis", 
                axis_pointer_type="cross",
                background_color="rgba(255, 255, 255, 0.9)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#333"),
                formatter=JsCode(
                    "function (params) {"
                    "    var colorSpan = color => '<span style=\"display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + color + '\"></span>';"
                    "    var date = params[0].name;"
                    "    var res = '<div style=\"margin: 0px 0 0;line-height:1.5;\"><div style=\"font-size:14px;color:#333;font-weight:bold;line-height:1.5;margin-bottom:7px;\">' + date + '</div>';"
                    "    params.forEach(param => {"
                    "        res += '<div style=\"color:#333;font-size:12px;margin-bottom:3px;\">' + colorSpan(param.color) + param.seriesName + ': ';"
                    "        if (param.seriesName === '日K') {"
                    "            res += '<strong>开盘:</strong> ' + param.value[0] + ' <strong>收盘:</strong> ' + param.value[1] + ' <strong>最低:</strong> ' + param.value[2] + ' <strong>最高:</strong> ' + param.value[3];"
                    "        } else {"
                    "            res += param.value;"
                    "        }"
                    "        res += '</div>';"
                    "    });"
                    "    return res;"
                    "}")
            ),
            datazoom_opts=[
                opts.DataZoomOpts(type_="inside", range_start=50, range_end=100),
                opts.DataZoomOpts(
                    type_="slider",
                    range_start=50,
                    range_end=100,
                    xaxis_index=[0],
                    is_zoom_lock=False,
                ),
                opts.DataZoomOpts(
                    type_="slider",
                    range_start=50,
                    range_end=100,
                    yaxis_index=[0],
                    orient="vertical",
                    pos_left="98%",
                ),
            ],
            legend_opts=opts.LegendOpts(
                is_show=True,
                pos_top="top",
                pos_right="10%",
                item_width=25,
                item_height=14,
                textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666"),
                border_width=0,
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                orient="horizontal",
                pos_right="10px",
                pos_top="10px",
                item_size=15,
                item_gap=10,
                feature={
                    "dataZoom": {"yAxisIndex": "none", "icon": {"zoom": "path://M0,13.5h26.9 M13.5,26.9V0 M32.1,13.5H58V58H13.5 V32.1", "back": "path://M22,1.4L9.9,13.5l12.3,12.3 M10.3,13.5H54.9v44.6 H10.3v-26"}},
                    "restore": {"icon": {"restore": "path://M3.8,33.4 M47.3,81.8c-19.6,0-35.5-15.9-35.5-35.5c0-19.6,15.9-35.5,35.5-35.5c19.6,0,35.5,15.9,35.5,35.5C82.8,65.9,66.9,81.8,47.3,81.8 M47.3,17.8c-15.7,0-28.4,12.7-28.4,28.4c0,15.7,12.7,28.4,28.4,28.4c15.7,0,28.4-12.7,28.4-28.4C75.8,30.5,63,17.8,47.3,17.8 M63.7,47.3c0,1.2-0.9,2.1-2.1,2.1H49.4v12.1c0,1.2-0.9,2.1-2.1,2.1l0,0c-1.2,0-2.1-0.9-2.1-2.1V49.4H33c-1.2,0-2.1-0.9-2.1-2.1l0,0c0-1.2,0.9-2.1,2.1-2.1h12.1V33c0-1.2,0.9-2.1,2.1-2.1l0,0c1.2,0,2.1,0.9,2.1,2.1v12.1h12.1C62.7,45.2,63.7,46.2,63.7,47.3L63.7,47.3z"}},
                    "saveAsImage": {"icon": {"saveAsImage": "path://M4.7,22.9L29.3,45.5L54.7,23.4M4.6,43.6L4.6,58L53.8,58L53.8,43.6M29.2,45.1L29.2,0"}},
                }
            ),
        )
    )
    
    # 添加移动平均线
    line = (
        Line()
        .add_xaxis(dates)
        .add_yaxis(
            "MA5",
            stock_data['MA5'].tolist(),
            is_smooth=True,
            is_symbol_show=False,
            symbol="circle",
            symbol_size=2,
            color="#e35e2c",
            linestyle_opts=opts.LineStyleOpts(width=1, opacity=1, type_="solid"),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "MA10",
            stock_data['MA10'].tolist(),
            is_smooth=True,
            is_symbol_show=False,
            symbol="circle",
            symbol_size=2,
            color="#2b3d6b",
            linestyle_opts=opts.LineStyleOpts(width=1, opacity=1, type_="solid"),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "MA20",
            stock_data['MA20'].tolist(),
            is_smooth=True,
            is_symbol_show=False,
            symbol="circle",
            symbol_size=2,
            color="#6ca0d8",
            linestyle_opts=opts.LineStyleOpts(width=1, opacity=1, type_="solid"),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            "MA30",
            stock_data['MA30'].tolist(),
            is_smooth=True,
            is_symbol_show=False,
            symbol="circle",
            symbol_size=2,
            color="#d88b6c",
            linestyle_opts=opts.LineStyleOpts(width=1, opacity=1, type_="solid"),
            label_opts=opts.LabelOpts(is_show=False),
        )
    )
    
    # 添加标记点
    markpoint_data = []
    for point in mid_points:
        # 创建标记点
        date_index = point["date_idx"]
        if date_index < len(dates):
            markpoint_data.append(
                opts.MarkPointItem(
                    name=str(point["value"]),
                    coord=[dates[date_index], point["value"]],
                    value=point["value"],
                    symbol="circle",
                    symbol_size=40,
                    itemstyle_opts=opts.ItemStyleOpts(color=point["color"]),
                )
            )
    
    # 设置标记点
    kline.set_series_opts(
        markpoint_opts=opts.MarkPointOpts(
            data=markpoint_data,
            label_opts=opts.LabelOpts(
                is_show=True,
                position="inside",
                font_size=12,
                font_weight="bold",
                color="white",
            )
        )
    )
    
    # 添加水平参考线
    kline.set_series_opts(
        markline_opts=opts.MarkLineOpts(
            data=[
                opts.MarkLineItem(y=upper_reference_line, name="上方参考线", 
                                  linestyle_opts=opts.LineStyleOpts(color="#ef232a", type_="dashed", width=1)),
                opts.MarkLineItem(y=lower_reference_line, name="下方参考线", 
                                  linestyle_opts=opts.LineStyleOpts(color="#ef232a", type_="dashed", width=1)),
            ],
            label_opts=opts.LabelOpts(is_show=True, position="end", formatter="{c}", font_size=12, color="#ef232a"),
        )
    )
    
    # 将K线图和移动平均线叠加
    kline.overlap(line)
    return kline

@app.route('/')
def index():
    # 获取所有股票文件
    stock_files = [f for f in os.listdir('stock-data') if f.endswith('.xlsx')]
    stock_list = [{'code': f.split('_')[0], 'name': f.split('_')[1].replace('.xlsx', '')} for f in stock_files]
    
    return render_template('index.html', stocks=stock_list)

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

@app.route('/stock2/<code>')
@app.route('/stock2/<code>/<ktype>')
def stock2_chart(code, ktype='day'):
    # 查找对应的股票文件
    stock_files = [f for f in os.listdir('stock-data') if f.startswith(code)]
    if not stock_files:
        return "股票代码不存在"
    
    file_path = os.path.join('stock-data', stock_files[0])
    stock_name = stock_files[0].split('_')[1].replace('.xlsx', '')
    
    # 读取数据
    stock_data = read_stock_data(file_path)
    
    # 根据K线类型处理数据
    if ktype == 'week':
        processed_data = process_weekly_data(stock_data)
        ktype_name = '周K'
    elif ktype == 'month':
        processed_data = process_monthly_data(stock_data)
        ktype_name = '月K'
    elif ktype == 'year':
        processed_data = process_yearly_data(stock_data)
        ktype_name = '年K'
    else:  # 默认日K
        processed_data = stock_data
        ktype_name = '日K'
    
    # 准备数据
    dates = processed_data['trade_date'].tolist()
    k_data = [[float(processed_data.loc[i, 'open']), 
               float(processed_data.loc[i, 'close']), 
               float(processed_data.loc[i, 'low']), 
               float(processed_data.loc[i, 'high'])] 
              for i in processed_data.index]
    
    # 计算移动平均线数据
    processed_data['MA5'] = processed_data['close'].rolling(5).mean()
    processed_data['MA10'] = processed_data['close'].rolling(10).mean()
    processed_data['MA20'] = processed_data['close'].rolling(20).mean()
    processed_data['MA30'] = processed_data['close'].rolling(30).mean()
    
    # 找出最高点和最低点，用于添加标记
    max_price_idx = processed_data['high'].idxmax()
    min_price_idx = processed_data['low'].idxmin()
    max_price = processed_data.loc[max_price_idx, 'high']
    min_price = processed_data.loc[min_price_idx, 'low']
    max_date = processed_data.loc[max_price_idx, 'trade_date']
    min_date = processed_data.loc[min_price_idx, 'trade_date']
    
    # 生成 ECharts 选项的 JavaScript 代码
    chart_js = f"""
    // 数据意义：开盘(open)，收盘(close)，最低(lowest)，最高(highest)
    var data0 = {{
        categoryData: {dates},
        values: {k_data}
    }};
    
    function calculateMA(dayCount) {{
        var result = [];
        for (var i = 0, len = data0.values.length; i < len; i++) {{
            if (i < dayCount) {{
                result.push('-');
                continue;
            }}
            var sum = 0;
            for (var j = 0; j < dayCount; j++) {{
                sum += data0.values[i - j][1];
            }}
            result.push(sum / dayCount);
        }}
        return result;
    }}
    
    option = {{
        title: {{
            text: '{stock_name} - {ktype_name}',
            left: 0
        }},
        tooltip: {{
            trigger: 'axis',
            axisPointer: {{
                type: 'cross'
            }}
        }},
        legend: {{
            data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30']
        }},
        grid: {{
            left: '10%',
            right: '10%',
            bottom: '15%'
        }},
        xAxis: {{
            type: 'category',
            data: data0.categoryData,
            scale: true,
            boundaryGap: false,
            axisLine: {{onZero: false}},
            splitLine: {{show: false}},
            splitNumber: 20,
            min: 'dataMin',
            max: 'dataMax'
        }},
        yAxis: {{
            scale: true,
            splitArea: {{
                show: true
            }}
        }},
        dataZoom: [
            {{
                type: 'inside',
                start: 50,
                end: 100
            }},
            {{
                show: true,
                type: 'slider',
                y: '90%',
                start: 50,
                end: 100
            }}
        ],
        series: [
            {{
                name: '日K',
                type: 'candlestick',
                data: data0.values,
                itemStyle: {{
                    normal: {{
                        color: upColor,
                        color0: downColor,
                        borderColor: upBorderColor,
                        borderColor0: downBorderColor
                    }}
                }},
                markPoint: {{
                    label: {{
                        normal: {{
                            formatter: function (param) {{
                                return param != null ? Math.round(param.value) : '';
                            }}
                        }}
                    }},
                    data: [
                        {{
                            name: '标记点',
                            coord: ['{max_date}', {max_price}],
                            value: {max_price},
                            itemStyle: {{
                                normal: {{color: 'rgb(41,60,85)'}}
                            }}
                        }},
                        {{
                            name: 'highest value',
                            type: 'max',
                            valueDim: 'highest'
                        }},
                        {{
                            name: 'lowest value',
                            type: 'min',
                            valueDim: 'lowest'
                        }},
                        {{
                            name: 'average value on close',
                            type: 'average',
                            valueDim: 'close'
                        }}
                    ],
                    tooltip: {{
                        formatter: function (param) {{
                            return param.name + '<br>' + (param.data.coord || '');
                        }}
                    }}
                }},
                markLine: {{
                    symbol: ['none', 'none'],
                    data: [
                        [
                            {{
                                name: 'from lowest to highest',
                                type: 'min',
                                valueDim: 'lowest',
                                symbol: 'circle',
                                symbolSize: 10,
                                label: {{
                                    normal: {{show: false}},
                                    emphasis: {{show: false}}
                                }}
                            }},
                            {{
                                type: 'max',
                                valueDim: 'highest',
                                symbol: 'circle',
                                symbolSize: 10,
                                label: {{
                                    normal: {{show: false}},
                                    emphasis: {{show: false}}
                                }}
                            }}
                        ],
                        {{
                            name: 'min line on close',
                            type: 'min',
                            valueDim: 'close'
                        }},
                        {{
                            name: 'max line on close',
                            type: 'max',
                            valueDim: 'close'
                        }}
                    ]
                }}
            }},
            {{
                name: 'MA5',
                type: 'line',
                data: calculateMA(5),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.5}}
                }}
            }},
            {{
                name: 'MA10',
                type: 'line',
                data: calculateMA(10),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.5}}
                }}
            }},
            {{
                name: 'MA20',
                type: 'line',
                data: calculateMA(20),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.5}}
                }}
            }},
            {{
                name: 'MA30',
                type: 'line',
                data: calculateMA(30),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.5}}
                }}
            }},
        ]
    }};
    """
    
    return render_template('stock2.html', chart=chart_js, stock_name=stock_name, ktype=ktype)

@app.route('/stock3/<code>')
@app.route('/stock3/<code>/<ktype>')
def stock3_chart(code, ktype='day'):
    # 查找对应的股票文件
    stock_files = [f for f in os.listdir('stock-data') if f.startswith(code)]
    if not stock_files:
        return "股票代码不存在"
    
    file_path = os.path.join('stock-data', stock_files[0])
    stock_name = stock_files[0].split('_')[1].replace('.xlsx', '')
    
    # 读取数据
    stock_data = read_stock_data_enhanced(file_path)
    
    # 根据K线类型处理数据
    if ktype == 'week':
        processed_data = process_weekly_data_with_volume(stock_data)
        ktype_name = '周K'
    elif ktype == 'month':
        processed_data = process_monthly_data_with_volume(stock_data)
        ktype_name = '月K'
    elif ktype == 'year':
        processed_data = process_yearly_data_with_volume(stock_data)
        ktype_name = '年K'
    else:  # 默认日K
        processed_data = stock_data
        ktype_name = '日K'
    
    # 添加技术指标
    processed_data = process_stock_data_with_indicators(processed_data)
    
    # 准备数据
    dates = processed_data['trade_date'].tolist()
    k_data = [[float(processed_data.loc[i, 'open']), 
               float(processed_data.loc[i, 'close']), 
               float(processed_data.loc[i, 'low']), 
               float(processed_data.loc[i, 'high'])] 
              for i in processed_data.index]
    
    # 成交量数据
    volume_data = processed_data['vol'].tolist()
    
    # 技术指标数据
    rsi_data = processed_data['RSI'].fillna(0).tolist()
    macd_data = processed_data['MACD'].fillna(0).tolist()
    macd_signal_data = processed_data['MACD_Signal'].fillna(0).tolist()
    macd_histogram_data = processed_data['MACD_Histogram'].fillna(0).tolist()
    
    # KDJ数据
    kdj_k_data = processed_data['KDJ_K'].fillna(0).tolist()
    kdj_d_data = processed_data['KDJ_D'].fillna(0).tolist()
    kdj_j_data = processed_data['KDJ_J'].fillna(0).tolist()
    
    # 布林带数据
    bb_upper_data = processed_data['BB_Upper'].fillna(0).tolist()
    bb_middle_data = processed_data['BB_Middle'].fillna(0).tolist()
    bb_lower_data = processed_data['BB_Lower'].fillna(0).tolist()
    
    # 找出最高点和最低点，用于添加标记
    max_price_idx = processed_data['high'].idxmax()
    min_price_idx = processed_data['low'].idxmin()
    max_price = processed_data.loc[max_price_idx, 'high']
    min_price = processed_data.loc[min_price_idx, 'low']
    max_date = processed_data.loc[max_price_idx, 'trade_date']
    min_date = processed_data.loc[min_price_idx, 'trade_date']
    
    # 生成 ECharts 选项的 JavaScript 代码
    chart_js = f"""
    // K线数据
    var data0 = {{
        categoryData: {dates},
        values: {k_data}
    }};
    
    // 成交量数据
    var volumeData = {volume_data};
    
    // 技术指标数据
    var rsiData = {rsi_data};
    var macdData = {macd_data};
    var macdSignalData = {macd_signal_data};
    var macdHistogramData = {macd_histogram_data};
    var kdjKData = {kdj_k_data};
    var kdjDData = {kdj_d_data};
    var kdjJData = {kdj_j_data};
    var bbUpperData = {bb_upper_data};
    var bbMiddleData = {bb_middle_data};
    var bbLowerData = {bb_lower_data};
    
    function calculateMA(dayCount) {{
        var result = [];
        for (var i = 0, len = data0.values.length; i < len; i++) {{
            if (i < dayCount) {{
                result.push('-');
                continue;
            }}
            var sum = 0;
            for (var j = 0; j < dayCount; j++) {{
                sum += data0.values[i - j][1];
            }}
            result.push(sum / dayCount);
        }}
        return result;
    }}
    
    option = {{
        title: {{
            text: '{stock_name} - {ktype_name}',
            left: 0
        }},
        tooltip: {{
            trigger: 'axis',
            axisPointer: {{
                type: 'cross'
            }}
        }},
        legend: {{
            data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30', '成交量', 'RSI', 'MACD', 'MACD信号', 'KDJ-K', 'KDJ-D', '布林上轨', '布林中轨', '布林下轨']
        }},
        grid: [
            {{
                left: '5%',
                right: '5%',
                height: '50%'
            }},
            {{
                left: '5%',
                right: '5%',
                top: '55%',
                height: '15%'
            }},
            {{
                left: '5%',
                right: '5%',
                top: '75%',
                height: '20%'
            }}
        ],
        xAxis: [
            {{
                type: 'category',
                data: data0.categoryData,
                scale: true,
                boundaryGap: false,
                axisLine: {{onZero: false}},
                splitLine: {{show: false}},
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax',
                axisPointer: {{
                    z: 100
                }}
            }},
            {{
                type: 'category',
                gridIndex: 1,
                data: data0.categoryData,
                scale: true,
                boundaryGap: false,
                axisLine: {{onZero: false}},
                axisTick: {{show: false}},
                splitLine: {{show: false}},
                axisLabel: {{show: false}},
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax'
            }},
            {{
                type: 'category',
                gridIndex: 2,
                data: data0.categoryData,
                scale: true,
                boundaryGap: false,
                axisLine: {{onZero: false}},
                axisTick: {{show: false}},
                splitLine: {{show: false}},
                axisLabel: {{show: false}},
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax'
            }}
        ],
        yAxis: [
            {{
                scale: true,
                splitArea: {{
                    show: true
                }}
            }},
            {{
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: {{show: false}},
                axisLine: {{show: false}},
                axisTick: {{show: false}},
                splitLine: {{show: false}}
            }},
            {{
                scale: true,
                gridIndex: 2,
                splitNumber: 4,
                axisLine: {{show: false}},
                axisTick: {{show: false}},
                splitLine: {{show: false}}
            }}
        ],
        dataZoom: [
            {{
                type: 'inside',
                xAxisIndex: [0, 1, 2],
                start: 70,
                end: 100
            }},
            {{
                show: true,
                xAxisIndex: [0, 1, 2],
                type: 'slider',
                top: '97%',
                start: 70,
                end: 100
            }}
        ],
        series: [
            {{
                name: '日K',
                type: 'candlestick',
                data: data0.values,
                itemStyle: {{
                    normal: {{
                        color: upColor,
                        color0: downColor,
                        borderColor: upBorderColor,
                        borderColor0: downBorderColor
                    }}
                }},
                markPoint: {{
                    label: {{
                        normal: {{
                            formatter: function (param) {{
                                return param != null ? Math.round(param.value) : '';
                            }}
                        }}
                    }},
                    data: [
                        {{
                            name: '最高值',
                            coord: ['{max_date}', {max_price}],
                            value: {max_price},
                            itemStyle: {{
                                normal: {{color: 'rgb(41,60,85)'}}
                            }}
                        }},
                        {{
                            name: '最低值',
                            coord: ['{min_date}', {min_price}],
                            value: {min_price},
                            itemStyle: {{
                                normal: {{color: 'rgb(41,60,85)'}}
                            }}
                        }}
                    ]
                }}
            }},
            {{
                name: 'MA5',
                type: 'line',
                data: calculateMA(5),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.8, color: '#c23531'}}
                }}
            }},
            {{
                name: 'MA10',
                type: 'line',
                data: calculateMA(10),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.8, color: '#2f4554'}}
                }}
            }},
            {{
                name: 'MA20',
                type: 'line',
                data: calculateMA(20),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.8, color: '#61a0a8'}}
                }}
            }},
            {{
                name: 'MA30',
                type: 'line',
                data: calculateMA(30),
                smooth: true,
                lineStyle: {{
                    normal: {{opacity: 0.8, color: '#d48265'}}
                }}
            }},
            {{
                name: '布林上轨',
                type: 'line',
                data: bbUpperData,
                lineStyle: {{
                    normal: {{opacity: 0.5, color: '#fac858', type: 'dashed'}}
                }}
            }},
            {{
                name: '布林中轨',
                type: 'line',
                data: bbMiddleData,
                lineStyle: {{
                    normal: {{opacity: 0.7, color: '#ee6666'}}
                }}
            }},
            {{
                name: '布林下轨',
                type: 'line',
                data: bbLowerData,
                lineStyle: {{
                    normal: {{opacity: 0.5, color: '#fac858', type: 'dashed'}}
                }}
            }},
            {{
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumeData.map(function (item, index) {{
                    var colorList = data0.values[index][1] > data0.values[index][0] ? upColor : downColor;
                    return {{
                        value: item,
                        itemStyle: {{
                            color: colorList
                        }}
                    }};
                }})
            }},
            {{
                name: 'RSI',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: rsiData,
                lineStyle: {{
                    normal: {{color: '#91c7ae'}}
                }},
                markLine: {{
                    silent: true,
                    data: [
                        {{yAxis: 30}},
                        {{yAxis: 70}}
                    ]
                }}
            }},
            {{
                name: 'MACD',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: macdData,
                lineStyle: {{
                    normal: {{color: '#749f83'}}
                }}
            }},
            {{
                name: 'MACD信号',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: macdSignalData,
                lineStyle: {{
                    normal: {{color: '#ca8622'}}
                }}
            }},
            {{
                name: 'MACD柱状',
                type: 'bar',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: macdHistogramData.map(function(item) {{
                    return {{
                        value: item,
                        itemStyle: {{
                            color: item >= 0 ? upColor : downColor
                        }}
                    }};
                }})
            }},
            {{
                name: 'KDJ-K',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: kdjKData,
                lineStyle: {{
                    normal: {{color: '#fc8452', opacity: 0.6}}
                }}
            }},
            {{
                name: 'KDJ-D',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: kdjDData,
                lineStyle: {{
                    normal: {{color: '#9a60b4', opacity: 0.6}}
                }}
            }}
        ]
    }};
    """
    
    return render_template('stock3.html', chart=chart_js, stock_name=stock_name, ktype=ktype)

if __name__ == '__main__':
    app.run(debug=True)