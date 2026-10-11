import requests
import re
import json
import pandas as pd
from datetime import datetime
import os

def fetch_silicon_data():
    url = 'https://www.silicondata.com/products/silicon-index'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text

    # 使用正则匹配所有指标的 title 和 points 数组
    pattern = r'"title":"([^"]+)".*?"points":(\[\{.*?\}\])'
    matches = re.findall(pattern, html)

    # 获取当前日期作为索引
    today_date = datetime.now().strftime('%Y-%m-%d')
    today_data = {'Date': today_date}

    for title, points_str in matches:
        try:
            points = json.loads(points_str)
            if points:
                # 获取数组中最新一天的价格
                latest_price = points[-1]['price']
                # 清洗一下 title，去掉括号内的 ticker 以保持列名整洁
                clean_title = title.split('(')[0].strip()
                today_data[clean_title] = latest_price
        except json.JSONDecodeError:
            continue

    return pd.DataFrame([today_data])

def update_datasets():
    df_new = fetch_silicon_data()
    csv_file = 'data.csv'
    excel_file = 'data.xlsx'

    # 如果存在历史数据，则读取并追加
    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        # 合并新数据，并按日期去重（如果当天已运行过，则覆盖更新）
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['Date'], keep='last')
    else:
        df_combined = df_new

    # 将日期排在第一列，并按日期排序
    cols = ['Date'] + [col for col in df_combined.columns if col != 'Date']
    df_combined = df_combined[cols].sort_values('Date')

    # 保存为 CSV (供看板渲染) 和 Excel (供直接下载)
    df_combined.to_csv(csv_file, index=False)
    df_combined.to_excel(excel_file, index=False)
    print(f"Data updated successfully for {df_new['Date'].iloc[0]}")

if __name__ == "__main__":
    update_datasets()
