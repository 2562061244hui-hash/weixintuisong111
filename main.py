import random
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import json

def get_color():
    return random.choice(["#FF69B4", "#FF1493", "#FF4500", "#FF6347", "#DB7093", "#00BFFF"])

def get_access_token(config):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config['app_id']}&secret={config['app_secret']}"
    try:
        res = get(url).json()
        return res.get('access_token')
    except:
        sys.exit(1)

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
        return "获取中", "N/A"

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
        return None

def send_message(to_user, token, config, weather_info):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    today = datetime.now().date()
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days
    
    # --- 合并生日逻辑 ---
    birthday_list = []
    for i in range(1, 10):
        key = f"birthday{i}"
        if key in config:
            v = config[key]
            diff = get_birthday_days(v["birthday"], today)
            if diff is not None:
                msg = f"{v['name']}生日快乐!🎂" if diff == 0 else f"{v['name']}倒计时{diff}天"
                birthday_list.append(msg)
    
    # 用换行符拼接，如果没人生日就给个保底
    tips_msg = "\n".join(birthday_list) if birthday_list else "今天也是爱你的一天！"

    # --- 构造报文 ---
    data_packet = {
        "love_day": {"value": str(love_days), "color": "#FF1493"},
        "region": {"value": str(config["region"]), "color": get_color()},
        "weather": {"value": str(weather_info[0]), "color": get_color()},
        "temp": {"value": str(weather_info[1]), "color": get_color()},
        "tips": {"value": tips_msg, "color": get_color()} # 这里换了名字
    }

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": data_packet
    }
    
    # 打印日志
    print(f"--- 准备发送 ---")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    res = post(url, json=body).json()
    print(f"--- 服务器反馈: {res} ---")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval("".join([line.split('#')[0] for line in f.readlines() if line.strip()]))

    token = get_access_token(config)
    weather = get_weather(config)
    
    for user in config["user"]:
        send_message(user, token, config, weather)
