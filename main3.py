from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import matplotlib.pyplot as plt
import requests
import platform

def decrypt_aes_ecb(encrypted_data: str) -> str:

key = encrypted_data[:16].encode('utf-8')
encrypted_data = encrypted_data[16:]
encrypted_data_bytes = base64.b64decode(encrypted_data)

cipher = AES.new(key, AES.MODE_ECB)

decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)

return decrypted_data.decode('utf-8')
idserial = ""
servicehall = ""
all_data = dict()

if name == "main":
# 读入账户信息
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

# 发送请求，得到加密后的字符串
url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2024-01-01&endtime=2024-12-31&idserial={idserial}&tradetype=-1"
cookie = {
    "servicehall": servicehall,
}
response = requests.post(url, cookies=cookie)

# 解密字符串
encrypted_string = json.loads(response.text)["data"]
decrypted_string = decrypt_aes_ecb(encrypted_string)

# 整理数据
data = json.loads(decrypted_string)
for item in data["resultData"]["rows"]:
    try:
        if item["mername"] in all_data:
            all_data[item["mername"]] += item["txamt"]
        else:
            all_data[item["mername"]] = item["txamt"]
    except Exception as e:
        pass
all_data = {k: round(v / 100, 2) for k, v in all_data.items()} # 将分转换为元，并保留两位小数
print(len(all_data))
# 输出结果
all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
if platform.system() == "Darwin":
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['SimHei']
plt.figure(figsize=(12, len(all_data) / 66 * 18))
colors = plt.cm.tab20([i / len(all_data) for i in range(len(all_data))])
plt.barh(list(all_data.keys()), list(all_data.values()), color=colors)
for index, value in enumerate(list(all_data.values())):
    plt.text(value + 0.01 * max(all_data.values()),
            index,
            str(value),
            va='center')
    
# 计算并输出总消费金额
total_amount = sum(all_data.values())

# plt.tight_layout()
plt.xlim(0, 1.2 * max(all_data.values()))
plt.title(f"华清大学食堂消费情况\n总消费金额: {total_amount} 元")
plt.xlabel("消费金额（元）")
plt.savefig("result.png")
plt.show()

# 统计每个食堂的总消费额
canteen_data = {}
for key, value in all_data.items():
    canteen_name = key.split('_')[0]
    if canteen_name in canteen_data:
        canteen_data[canteen_name] += value
    else:
        canteen_data[canteen_name] = value

# 生成每个食堂的总消费额统计图
canteen_data = dict(sorted(canteen_data.items(), key=lambda x: x[1], reverse=False))
canteen_data = {k: round(v, 2) for k, v in canteen_data.items()}  # 四舍五入保留两位小数
plt.figure(figsize=(12, len(canteen_data) / 66 * 18))
colors = plt.cm.tab20([i / len(canteen_data) for i in range(len(canteen_data))])
plt.barh(list(canteen_data.keys()), list(canteen_data.values()), color=colors)
for index, value in enumerate(list(canteen_data.values())):
    plt.text(value + 0.01 * max(canteen_data.values()),
            index,
            str(value),
            va='center')
    
# plt.tight_layout()
plt.xlim(0, 1.2 * max(canteen_data.values()))
plt.title(f"华清大学各食堂总消费情况\n总消费金额: {total_amount} 元")
plt.xlabel("消费金额（元）")
plt.savefig("canteen_total_expenses.png")
plt.show()

# 生成每个食堂的总消费额圆饼图
plt.figure(figsize=(10, 10))

# 对数据进行排序
sorted_data = sorted(canteen_data.items(), key=lambda x: x[1], reverse=True)

# 将最后三项合并为others
if len(sorted_data) > 3:
    others = sum([item[1] for item in sorted_data[-3:]])
    sorted_data = sorted_data[:-3] + [('others', others)]

labels, values = zip(*sorted_data)
colors = plt.cm.tab20([i / len(values) for i in range(len(values))])
plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
plt.title(f"华清大学各食堂总消费情况\n总消费金额: {total_amount} 元")
plt.savefig("canteen_total_expenses_pie.png")
plt.show()
