import os
import paramiko
import requests
import json
from datetime import datetime, timezone, timedelta

def ssh_multiple_connections(hosts_info, command):
    users = []
    hostnames = []
    statuses = []  # Store the login status (success or failure) for each connection
    for host_info in hosts_info:
        hostname = host_info['hostname']
        username = host_info['username']
        password = host_info['password']
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname, port=10345, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(command)
            user = stdout.read().decode().strip()
            users.append(user)
            hostnames.append(hostname)
            statuses.append('成功')  # Login was successful
            ssh.close()
        except Exception as e:
            print(f"用户：{username}，连接 {hostname} 时出错: {str(e)}")
            users.append('N/A')  # Indicating no user could be fetched
            hostnames.append(hostname)
            statuses.append(f'失败: {str(e)}')  # Login failed and include error message
    return users, hostnames, statuses

# Get SSH info from environment variable
ssh_info_str = os.getenv('SSH_INFO', '[]')
hosts_info = json.loads(ssh_info_str)

command = 'whoami'
user_list, hostname_list, status_list = ssh_multiple_connections(hosts_info, command)

# Prepare the content to be sent in the push message
content = "SSH服务器登录信息：\n"
for user, hostname, status in zip(user_list, hostname_list, status_list):
    content += f"服务器：{hostname}，用户名：{user}，登录状态：{status}\n"

beijing_timezone = timezone(timedelta(hours=8))
time = datetime.now(beijing_timezone).strftime('%Y-%m-%d %H:%M:%S')

# Get the menu for Telegram and the current login IP
menu = requests.get('https://api.zzzwb.com/v1?get=tg').json()
loginip = requests.get('https://api.ipify.org?format=json').json()['ip']
content += f"本次登录时间：{time}\n登录IP：{loginip}"

push = os.getenv('PUSH')

def mail_push(url):
    data = {
        "body": content,
        "email": os.getenv('MAIL')
    }

    response = requests.post(url, json=data)

    try:
        response_data = json.loads(response.text)
        if response_data['code'] == 200:
            print("推送成功")
        else:
            print(f"推送失败，错误代码：{response_data['code']}")
    except json.JSONDecodeError:
        print("连接邮箱服务器失败了")

def telegram_push(message):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        'text': message,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps({
            "inline_keyboard": menu,
            "one_time_keyboard": True
         })
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"发送消息到Telegram失败: {response.text}")

if push == "mail":
    mail_push('https://zzzwb.pp.ua/test')
elif push == "telegram":
    telegram_push(content)
else:
    print("推送失败，推送参数设置错误")
