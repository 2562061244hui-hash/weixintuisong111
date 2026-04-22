import random
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import json

def get_color():
    return random.choice(["#FF69B4", "#FF1493", "#FF4500", "#FF6347", "#00BFFF"])

def get_access_token(config):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config['app_id']}&secret={config['app_secret']}"
    res = get(url).json()
    token = res.get('access_token')
    if not token:
        print(f"Token获取失败，请检查appid和secret: {res}")
        sys.exit(1)
    return token

def get_weather(config):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key, region = config["weather_key"], config["region"]
    try:
        r_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
        city_id = get(r_url, headers=headers).json()["location"][0]["id"]
        w_url = f"https://devapi.qweather.com/v7/weather/now?location={city_id}&key={key}"
        res = get(w_url, headers=headers).json()["now"]
        return res["text"], res["temp"] + "°C"
    except:
        return "数据获取中", "N/A"

def get_birthday_days(birthday_str, today):
    year = today.year
    is_lunar = birthday_str.startswith("r")
    clean_date = birthday_str.replace("r", "")
    try:
        parts = clean_date.split("-")
        m, d = int(parts[1]), int(parts[2])
        if is_lunar:
            target = ZhDate(year, m, d).to_datetime().date()
            if today > target: target = ZhDate(year + 1, m, d).to_datetime().date()
        else:
            target = date(year, m, d)
            if today > target: target = date(year + 1, m, d)
        return (target - today).days
    except:
        return "计算中"

def send_message(to_user, token, config, weather_info):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    today = datetime.now().date()
    
    # 核心数据计算
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days
    
    # 生日逻辑保底
    try:
        b1_days = get_birthday_days(config["birthday1"]["birthday"], today)
        b1_text = f"今天{config['birthday1']['name']}生日!🎂" if b1_days == 0 else f"{config['birthday1']['name']}生日倒计时 {b1_days}天"
    except:
        b1_text = "生日信息加载中"

    try:
        b2_days = get_birthday_days(config["birthday2"]["birthday"], today)
        b2_text = f"今天{config['birthday2']['name']}生日!🎂" if b2_days == 0 else f"{config['birthday2']['name']}生日倒计时 {b2_days}天"
    except:
        b2_text = "生日信息加载中"

    # 显式构造发送数据（确保 Key 与模板 {{key.DATA}} 一一对应）
    data_packet = {
        "date": {"value": f"{today.year}年{today.month}月{today.day}日", "color": get_color()},
        "love_day": {"value": str(love_days), "color": "#FF1493"},
        "region": {"value": str(config["region"]), "color": get_color()},
        "weather": {"value": str(weather_info[0]), "color": get_color()},
        "temp": {"value": str(weather_info[1]), "color": get_color()},
        "birthday1": {"value": b1_text, "color": get_color()},
        "birthday2": {"value": b2_text, "color": get_color()}
    }

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": data_packet
    }
    
    # 调试日志：非常重要
    print(f"--- 正在向微信发送数据 ---")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    
    res = post(url, json=body).json()
    print(f"--- 微信返回结果: {res} ---")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        # 去除可能的空行和注释
        content = "".join([line.split('#')[0] for line in f.readlines() if line.strip()])
        config = eval(content)

    token = get_access_token(config)
    weather = get_weather(config)
    
    for user in config["user"]:
        send_message(user, token, config, weather)
