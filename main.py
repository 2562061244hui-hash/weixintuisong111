import random
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)

def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        response = get(post_url).json()
        if 'access_token' in response:
            return response['access_token']
        else:
            print(f"获取access_token失败: {response}")
            sys.exit(1)
    except Exception as e:
        print(f"网络请求错误: {e}")
        sys.exit(1)

def get_weather(config, region):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    response = get(region_url, headers=headers).json()
    
    if response["code"] != "200":
        print(f"城市查询失败，代码: {response['code']}")
        sys.exit(1)
    
    location_id = response["location"][0]["id"]
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    res = get(weather_url, headers=headers).json()
    
    weather = res["now"]["text"]
    temp = res["now"]["temp"] + "°C"
    wind_dir = res["now"]["windDir"]
    return weather, temp, wind_dir

def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_month = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            birthday_date = ZhDate(year, r_month, r_day).to_datetime().date()
        except Exception:
            return "日期错误"
        year_date = birthday_date
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)

    if today > year_date:
        if birthday_year[0] == "r":
            new_date = ZhDate((year + 1), r_month, r_day).to_datetime().date()
            birth_date = date((year + 1), new_date.month, new_date.day)
        else:
            birth_date = date((year + 1), int(birthday.split("-")[1]), int(birthday.split("-")[2]))
        diff = (birth_date - today).days
    elif today == year_date:
        diff = 0
    else:
        diff = (year_date - today).days
    return diff

def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    r = get(url)
    return r.json()["note"], r.json()["content"]

def send_message(to_user, access_token, config, region_name, weather, temp, wind_dir, note_ch, note_en):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    
    now = datetime.now()
    today = now.date()
    week = week_list[now.isoweekday() % 7]
    
    love_date_str = config["love_date"]
    love_date = datetime.strptime(love_date_str, "%Y-%m-%d").date()
    love_days = (today - love_date).days

    birthdays = {k: v for k, v in config.items() if k.startswith("birth")}
    
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "region": {"value": region_name, "color": get_color()},
            "weather": {"value": weather, "color": get_color()},
            "temp": {"value": temp, "color": get_color()},
            "wind_dir": {"value": wind_dir, "color": get_color()},
            "love_day": {"value": str(love_days), "color": get_color()},
            "note_en": {"value": note_en, "color": get_color()},
            "note_ch": {"value": note_ch, "color": get_color()}
        }
    }

    for key, value in birthdays.items():
        diff = get_birthday(value["birthday"], today.year, today)
        if diff == 0:
            msg = f"今天{value['name']}生日哦，祝{value['name']}生日快乐！"
        else:
            msg = f"距离{value['name']}的生日还有{diff}天"
        data["data"][key] = {"value": msg, "color": get_color()}

    res = post(url, json=data).json()
    print(f"用户 {to_user} 推送结果: {res}")

if __name__ == "__main__":
    # 读取配置，尝试兼容 config.txt 或 config.json
    filename = "config.txt" if os.path.exists("config.txt") else "config.json"
    try:
        with open(filename, encoding="utf-8") as f:
            # 这里的 eval 要求文件内容必须是合法的 Python 字典格式且无注释
            config = eval(f.read())
    except Exception as e:
        print(f"配置文件读取失败: {e}")
        sys.exit(1)

    token = get_access_token(config)
    weather, temp, wind = get_weather(config, config["region"])
    
    note_ch = config.get("note_ch", "")
    note_en = config.get("note_en", "")
    if not note_ch:
        note_ch, note_en = get_ciba()

    for user in config["user"]:
        send_message(user, token, config, config["region"], weather, temp, wind, note_ch, note_en)
