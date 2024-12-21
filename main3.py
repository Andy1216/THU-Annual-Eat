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
count_data = dict()

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
    
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2024-01-01&endtime=2024-12-31&idserial={idserial}&tradetype=-1"
    cookie = {
        "servicehall": servicehall,
    }
    response = requests.post(url, cookies=cookie)
    encrypted_string = json.loads(response.text)["data"]
    decrypted_string = decrypt_aes_ecb(encrypted_string)
    data = json.loads(decrypted_string)

    for item in data["resultData"]["rows"]:
        try:
            mername = item["mername"]
            txamt = item["txamt"]

            if mername in all_data:
                all_data[mername] += txamt
                count_data[mername] += 1
            else:
                all_data[mername] = txamt
                count_data[mername] = 1
        except Exception as e:
            pass
    
    # Convert to yuan and round to 2 decimal places
    all_data = {k: round(v / 100, 2) for k, v in all_data.items()}
    # Calculate average spending
    avg_data = {k: round(all_data[k] / count_data[k], 2) for k in all_data}

    print(f"Total entries processed: {len(all_data)}")

    # Sort the data by total amount, number of transactions, and average spending
    all_data_sorted = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=True))
    count_data_sorted = dict(sorted(count_data.items(), key=lambda x: x[1], reverse=True))
    avg_data_sorted = dict(sorted(avg_data.items(), key=lambda x: x[1], reverse=True))

    # Set font for Chinese characters
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif platform.system() == "Linux":
        plt.rcParams['font.family'] = ['Droid Sans Fallback', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']

    # Function to create and save a bar chart with data sorted from top (largest) to bottom (smallest)
    def create_bar_chart(data, title, xlabel, filename):
        plt.figure(figsize=(12, len(data) / 66 * 18))
        
        # Convert the dictionary items to lists and reverse them for top-to-bottom order
        keys, values = zip(*data.items())
        keys = list(keys)[::-1]  # Reverse the keys for top-to-bottom order
        values = list(values)[::-1]  # Reverse the values for top-to-bottom order
        
        plt.barh(keys, values)
        
        # Add value labels to the bars
        for index, value in enumerate(values):
            plt.text(value + 0.01 * max(values),  # Offset the text slightly to the right of the bar
                    index,  # Position the text vertically at the center of each bar
                    str(value),
                    va='center')
        
        plt.xlim(0, 1.2 * max(values))  # Set x-axis limit to accommodate all bars with some padding
        plt.title(title)
        plt.xlabel(xlabel)
        plt.tight_layout()  # Adjust layout to fit everything nicely on the canvas
        plt.savefig(filename)  # Save the figure to a file
        plt.show()  # Display the plot

    # Plot total spending
    create_bar_chart(all_data_sorted, "华清大学食堂消费总量情况", "消费金额（元）", "total_spending.png")

    # Plot number of transactions
    create_bar_chart(count_data_sorted, "华清大学食堂消费次数情况", "消费次数", "transaction_counts.png")

    # Plot average spending
    create_bar_chart(avg_data_sorted, "华清大学食堂平均消费价格情况", "平均消费金额（元）", "average_spending.png")
