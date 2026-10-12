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
    clean_html = response.text.replace('\\"', '"')

    pattern = r'"group":"[^"]+","title":"([^"]+)".*?"rawValue":"([^"]+)"'
    matches = re.findall(pattern, clean_html)

    today_date = datetime.now().strftime('%Y-%m-%d')
    today_data = {'Date': today_date}

    for title, price in matches:
        clean_title = title.split('(')[0].strip()
        
        # 根据指标名称分配相应的单位后缀
        if clean_title in ['H100', 'H100-hyperscaler', 'A100', 'A100-hyperscaler', 'B200', 'B300', 'MI300X', 'H200']:
            final_title = f"{clean_title} (USD / GPU-hour)"
        elif clean_title == 'GDDR6':
            final_title = "GDDR6 (USD / GB)"
        elif clean_title in ['LLM Token', 'Open LLM', 'Proprietary LLM']:
            final_title = f"{clean_title} (USD / M tokens)"
        else:
            final_title = clean_title

        if final_title not in today_data:
            try:
                # 强制保留两位小数存储
                today_data[final_title] = round(float(price), 2)
            except ValueError:
                continue

    return pd.DataFrame([today_data])

def update_datasets():
    df_new = fetch_silicon_data()
    
    if len(df_new.columns) <= 1:
        print("未抓取到有效价格数据，请检查网页结构。")
        return

    csv_file = 'data.csv'
    excel_file = 'data.xlsx'

    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['Date'], keep='last')
    else:
        df_combined = df_new

    # 将硬件指标、内存指标和 Token 指标分开
    hardware_cols = [col for col in df_combined.columns if 'GPU-hour' in col]
    ram_cols = [col for col in df_combined.columns if 'GB' in col]
    token_cols = [col for col in df_combined.columns if 'tokens' in col]
    
    # 按预定顺序拼接列
    final_cols = ['Date'] + hardware_cols + ram_cols + token_cols
    
    # 只提取实际存在的列（防止由于某天数据抓取缺失导致报错）
    final_cols = [col for col in final_cols if col in df_combined.columns]
    df_combined = df_combined[final_cols].sort_values('Date')

    # 将所有数字格式化为两位小数，确保保存的 CSV 和 Excel 视觉一致性
    for col in df_combined.columns:
        if col != 'Date':
            df_combined[col] = df_combined[col].apply(lambda x: f"{float(x):.2f}" if pd.notnull(x) else "")

    df_combined.to_csv(csv_file, index=False)
    df_combined.to_excel(excel_file, index=False)
    print(f"数据更新成功，日期: {df_new['Date'].iloc[0]}。")

if __name__ == "__main__":
    update_datasets()
