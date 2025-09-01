
import requests
import pandas as pd
from datetime import datetime

# 获取东方财富行业板块数据
def get_sector_data():
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "50",
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f12,f14,f3,f62"
    }
    res = requests.get(url, params=params)
    data = res.json()["data"]["diff"]
    df = pd.DataFrame(data)
    df.rename(columns={
        "f12": "板块代码",
        "f14": "板块名称",
        "f3": "涨幅(%)",
        "f62": "主力资金流入(万)"
    }, inplace=True)
    return df

# 获取北向资金数据
def get_northbound():
    url = "http://push2.eastmoney.com/api/qt/kamt/get"
    params = {"fields": "hk2sh,hk2sz,sh2hk,sz2hk"}
    res = requests.get(url, params=params).json()
    return res["data"]

# 生成雷达表
def generate_radar_table():
    df_sector = get_sector_data()
    north = get_northbound()
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 筛选热度前5板块
    df_top = df_sector.sort_values(by="涨幅(%)", ascending=False).head(5)
    df_top["日期"] = date_str

    # 添加北向资金汇总
    df_top["北向资金流入(亿)"] = (north["hk2sh"] + north["hk2sz"]) / 1e8

    # 输出 Excel
    output_path = f"板块轮动雷达表_{date_str}.xlsx"
    df_top.to_excel(output_path, index=False)
    print(f"已生成雷达表: {output_path}")

if __name__ == "__main__":
    generate_radar_table()
