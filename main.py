import random
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

def get_color():
    # 选取一些温馨的颜色
    return random.choice(["#FF69B4", "#FF1493", "#FF4500", "#FF6347", "#DB7093"])

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
        return res["text"], res["temp"] + "°"
    except:
        return "查询失败", "N/A"

def get_birthday(b_str, today):
    year = today.year
    is_lunar = b_str.startswith("r")
    clean_date = b_str.replace("r", "")
    try:
        m, d = map(int, clean_date.split("-")[1:3])
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
    
    # 构造两行生日提醒
    memo_list = []
    # 按照 birthday1, birthday2 的顺序排列
    for i in range(1, 10):
        key = f"birthday{i}"
        if key in config:
            v = config[key]
            diff = get_birthday(v["birthday"], today)
            if diff is not None:
                msg = f"{v['name']}生日快乐!🎂" if diff == 0 else f"{v['name']}生日还有{diff}天"
                memo_list.append(msg)
    
    # 用 \n 连接，实现微信端分行显示
    memo_text = "\n".join(memo_list) if memo_list else "今天也要开心呀 ❤️"

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": f"{today.month}月{today.day}日", "color": get_color()},
            "love_day": {"value": str(love_days), "color": "#FF1493"},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_info[0], "color": get_color()},
            "temp": {"value": weather_info[1], "color": get_color()},
            "memo": {"value": memo_text, "color": get_color()}
        }
    }
    res = post(url, json=body).json()
    print(f"To {to_user}: {res}")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        content = "".join([line.split('#')[0] for line in f.readlines()])
        config = eval(content)

    token = get_access_token(config)
    weather = get_weather(config)
    
    for user in config["user"]:
        send_message(user, token, config, weather)
