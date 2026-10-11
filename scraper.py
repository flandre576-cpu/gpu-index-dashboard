import requests
import re
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
    
    # 关键修复：清洗 RSC 格式中被转义的反斜杠引号，还原为标准 JSON 字符串
    clean_html = response.text.replace('\\"', '"')

    # 优化后的正则：直接提取指标名称和最新的 rawValue
    pattern = r'"title":"([^"]+)".*?"rawValue":"([^"]+)"'
    matches = re.findall(pattern, clean_html)

    today_date = datetime.now().strftime('%Y-%m-%d')
    today_data = {'Date': today_date}

    for title, price in matches:
        # 清洗指标名称，去掉括号部分 (例如: H100(SDH100RT) -> H100)
        clean_title = title.split('(')[0].strip()
        
        # 防止重复读取，仅保留第一次匹配到的干净数据
        if clean_title not in today_data:
            try:
                today_data[clean_title] = float(price)
            except ValueError:
                continue

    return pd.DataFrame([today_data])

def update_datasets():
    df_new = fetch_silicon_data()
    
    # 如果没有抓取到除了 Date 以外的任何数据，则直接退出，防止写入空数据
    if len(df_new.columns) <= 1:
        print("未抓取到有效价格数据，请检查网页结构。")
        return

    csv_file = 'data.csv'
    excel_file = 'data.xlsx'

    # 如果存在历史数据，则读取并追加
    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        # 合并新数据，并按日期去重（如果当天已运行过，则覆盖更新为最新值）
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['Date'], keep='last')
    else:
        df_combined = df_new

    # 将日期排在第一列，并按日期排序
    cols = ['Date'] + [col for col in df_combined.columns if col != 'Date']
    df_combined = df_combined[cols].sort_values('Date')

    # 保存为 CSV (供看板渲染) 和 Excel (供直接下载)
    df_combined.to_csv(csv_file, index=False)
    df_combined.to_excel(excel_file, index=False)
    print(f"数据更新成功，日期: {df_new['Date'].iloc[0]}，共记录 {len(df_new.columns)-1} 个指标。")

if __name__ == "__main__":
    update_datasets()
