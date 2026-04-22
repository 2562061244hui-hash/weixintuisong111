import random
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

def get_color():
    return random.choice(["#FFB6C1", "#87CEFA", "#98FB98", "#DDA0DD", "#FFD700", "#FF6347", "#00CED1"])

def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        return get(url).json()['access_token']
    except Exception as e:
        print(f"Token Error: {e}")
        sys.exit(1)

def get_weather(config):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key = config["weather_key"]
    region = config["region"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    try:
        city_data = get(region_url, headers=headers).json()
        if city_data["code"] != "200":
            return "位置未知", "N/A", "无"
        location_id = city_data["location"][0]["id"]
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
        res = get(weather_url, headers=headers).json()
        return res["now"]["text"], res["now"]["temp"] + "°C", res["now"]["windDir"]
    except:
        return "获取失败", "N/A", "无"

def get_birthday_days(birthday_str, today):
    year = today.year
    is_lunar = birthday_str.startswith("r")
    clean_date = birthday_str.replace("r", "")
    try:
        parts = clean_date.split("-")
        month, day = int(parts[1]), int(parts[2])
        if is_lunar:
            target = ZhDate(year, month, day).to_datetime().date()
            if today > target:
                target = ZhDate(year + 1, month, day).to_datetime().date()
        else:
            target = date(year, month, day)
            if today > target:
                target = date(year + 1, month, day)
        return (target - today).days
    except:
        return None

def send_message(to_user, token, config, weather_info, note):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    today = datetime.now().date()
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[datetime.now().isoweekday() % 7]
    
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days

    # 合并所有生日信息
    birthday_msg = ""
    for k, v in config.items():
        if k.startswith("birthday"):
            diff = get_birthday_days(v["birthday"], today)
            if diff is not None:
                msg = f"今天{v['name']}生日啦！🎂" if diff == 0 else f"距离{v['name']}生日还有{diff}天"
                birthday_msg += msg + "\n"

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "https://www.qweather.com/",
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_info[0], "color": get_color()},
            "temp": {"value": weather_info[1], "color": get_color()},
            "wind_dir": {"value": weather_info[2], "color": get_color()},
            "love_day": {"value": str(love_days), "color": "#FF1493"},
            "birthday": {"value": birthday_msg.strip(), "color": get_color()},
            "note_ch": {"value": note[0], "color": get_color()},
            "note_en": {"value": note[1], "color": get_color()}
        }
    }
    res = post(url, json=body).json()
    print(f"To {to_user}: {res}")

if __name__ == "__main__":
    conf_path = "config.txt"
    with open(conf_path, "r", encoding="utf-8") as f:
        content = "".join([line.split('#')[0] for line in f.readlines()])
        config = eval(content)

    token = get_access_token(config)
    weather = get_weather(config)
    
    try:
        cb = get("http://open.iciba.com/dsapi/").json()
        note = (config.get("note_ch") or cb["note"], config.get("note_en") or cb["content"])
    except:
        note = ("每天都要开心哦！", "Keep smiling every day!")

    for user in config["user"]:
        send_message(user, token, config, weather, note)
