import os
import json
import requests
import matplotlib.pyplot as plt
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from datetime import datetime, timedelta
from matplotlib.animation import FuncAnimation
import random

# 解密函数
def decrypt_aes_ecb(encrypted_data: str) -> str:
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)
    return decrypted_data.decode('utf-8')

# 获取每日日期范围
def get_daily_ranges(start_date, end_date):
    daily_ranges = []
    current_date = start_date
    while current_date <= end_date:
        daily_ranges.append(current_date)
        current_date += timedelta(days=1)
    return daily_ranges

# 请求并解密数据
def fetch_daily_data(idserial, servicehall, current_date):
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime={current_date}&endtime={current_date}&idserial={idserial}&tradetype=-1"
    cookie = {"servicehall": servicehall}
    response = requests.post(url, cookies=cookie)
    encrypted_string = json.loads(response.text).get("data", "")
    decrypted_string = decrypt_aes_ecb(encrypted_string)
    return json.loads(decrypted_string)

# 数据整理与累计
def process_data(data, all_data):
    for item in data["resultData"]["rows"]:
        try:
            if item["mername"] in all_data:
                all_data[item["mername"]] += item["txamt"]
            else:
                all_data[item["mername"]] = item["txamt"]
        except Exception as e:
            pass

# 数据合并函数
def merge_data(all_data):
    merged_data = {}
    for key in all_data.keys():
        brief_key = key.split('_')[0]
        if brief_key in merged_data:
            merged_data[brief_key] += all_data[key]
        else:
            merged_data[brief_key] = all_data[key]
    return merged_data

# 插值函数
def interpolate_data(prev_data, next_data, alpha):
    """在两帧数据之间插值"""
    all_keys = set(prev_data.keys()).union(next_data.keys())
    interpolated = {}
    for key in all_keys:
        prev_value = prev_data.get(key, 0)
        next_value = next_data.get(key, 0)
        interpolated[key] = prev_value + (next_value - prev_value) * alpha
    return interpolated

# 生成插值帧
def generate_interpolated_frames(data_list, dates, num_interpolation_frames=10):
    """生成插值帧"""
    interpolated_frames = []
    interpolated_dates = []
    for i in range(len(data_list) - 1):
        interpolated_frames.append(data_list[i])
        interpolated_dates.append(dates[i])
        for j in range(1, num_interpolation_frames):
            alpha = j / num_interpolation_frames
            frame = interpolate_data(data_list[i], data_list[i + 1], alpha)
            interpolated_frames.append(frame)
            interpolated_dates.append(dates[i + 1])
    interpolated_frames.append(data_list[-1])
    interpolated_dates.append(dates[-1])
    return interpolated_frames, interpolated_dates

# 动图生成
def create_animation(all_data_list, interpolated_dates, output_file):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体
    fig, ax = plt.subplots(figsize=(12, 8))

    # 分配初始食堂颜色
    colors = {}

    def update(frame):
        ax.clear()
        data = merge_data(all_data_list[frame])
        data = {k: round(v / 100, 2) for k, v in data.items()}
        data = dict(sorted(data.items(), key=lambda x: x[1], reverse=False))

        # 动态为新出现的食堂分配颜色
        for key in data.keys():
            if key not in colors:
                colors[key] = (random.random(), random.random(), random.random())

        keys = list(data.keys())
        values = list(data.values())
        bar_colors = [colors[key] for key in keys]

        ax.barh(keys, values, color=bar_colors)
        for index, value in enumerate(values):
            ax.text(value + 0.01 * max(values), index, str(value), va='center')

        total = sum(values)
        date_str = interpolated_dates[frame].strftime("%Y年%m月%d日")
        ax.set_title(f"累计消费情况 - 截至 {date_str}（总计：{round(total, 2)}元）", fontsize=20)
        ax.set_xlabel("消费金额（元）", fontsize=20)

    ani = FuncAnimation(fig, update, frames=len(all_data_list), repeat=False)
    ani.save(output_file, fps=30, writer='pillow')

# 主程序
if __name__ == "__main__":
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            account = json.load(f)
            idserial = account["idserial"]
            servicehall = account["servicehall"]
    except Exception as e:
        print("账户信息读取失败，请重新输入")
        idserial = input("请输入学号: ")
        servicehall = input("请输入服务代码: ")
        with open("config.json", "w", encoding='utf-8') as f:
            json.dump({"idserial": idserial, "servicehall": servicehall}, f, indent=4)

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    daily_ranges = get_daily_ranges(start_date, end_date)

    all_data = {}
    all_data_list = []

    for current_date in daily_ranges:
        data = fetch_daily_data(idserial, servicehall, current_date.strftime("%Y-%m-%d"))
        process_data(data, all_data)
        all_data_list.append(all_data.copy())

    interpolated_frames, interpolated_dates = generate_interpolated_frames(all_data_list, daily_ranges, num_interpolation_frames=10)

    create_animation(interpolated_frames, interpolated_dates, "daily_consumption_interpolated_colored.gif")
    print("动图已保存为 daily_consumption_interpolated_colored.gif")
