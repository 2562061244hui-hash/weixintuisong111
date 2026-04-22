import random
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys

def get_color():
    return random.choice(["#FF69B4", "#FF1493", "#FF4500", "#FF6347", "#DB7093", "#00BFFF"])

def get_access_token(config):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config['app_id']}&secret={config['app_secret']}"
    try:
        return get(url).json().get('access_token')
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
        return "查询失败", "N/A"

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
        return "数据错误"

def send_message(to_user, token, config, weather_info):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    today = datetime.now().date()
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days
    
    # 显式计算两个生日，确保变量名与模板 {{birthday1.DATA}} {{birthday2.DATA}} 严格对应
    b1_days = get_birthday_days(config["birthday1"]["birthday"], today)
    b1_msg = f"今天{config['birthday1']['name']}生日!🎂" if b1_days == 0 else f"距离{config['birthday1']['name']}生日还有{b1_days}天"
    
    b2_days = get_birthday_days(config["birthday2"]["birthday"], today)
    b2_msg = f"今天{config['birthday2']['name']}生日!🎂" if b2_days == 0 else f"距离{config['birthday2']['name']}生日还有{b2_days}天"

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": f"{today.year}年{today.month}月{today.day}日", "color": get_color()},
            "love_day": {"value": str(love_days), "color": "#FF1493"},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_info[0], "color": get_color()},
            "temp": {"value": weather_info[1], "color": get_color()},
            "birthday1": {"value": b1_msg, "color": get_color()},
            "birthday2": {"value": b2_msg, "color": get_color()}
        }
    }
    res = post(url, json=body).json()
    print(f"To {to_user}: {res}")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval("".join([line.split('#')[0] for line in f.readlines()]))

    token = get_access_token(config)
    weather = get_weather(config)
    
    for user in config["user"]:
        send_message(user, token, config, weather)
