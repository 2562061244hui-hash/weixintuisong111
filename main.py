import random
from time import localtime
from requests import get, post
from datetime import datetime, date

import sys
import os

def get_color():
    # 随机生成鲜亮的颜色
    return random.choice(["#FFB6C1", "#87CEFA", "#98FB98", "#DDA0DD", "#FFD700", "#FF6347", "#00CED1"])

def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        返回get(url).json['access_token']
    except Exception as e:
        print(f"Token获取失败: {e}")
        sys.exit(1)

def get_weather(config):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key = config["weather_key"]
    region = config["region"]
    # 获取城市ID
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    city_data = get(region_url, headers=headers).json()
    如果city_data["code"] != "200":
        返回 "未知", "N/A", "无"
    location_id = city_data["location"][0]["id"]
    # 获取天气
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    res = get(weather_url, headers=headers).json()
    返回res["现在"]["文本"], res["现在"]["temp"] + "°C", res["现在"]["风向"

def get_birthday_days(birthday_str, today):
    year = today.year
    is_lunar = birthday_str.startswith("r")
    clean_date = birthday_str.replace("r", "")
    month, day = map(int, clean_date.split("-")[1:3])

    try:
        if is_lunar:
            target = ZhDate(year, month, day).to_datetime().date()
            if today > target:
                target = ZhDate(year + 1, month, day).to_datetime().date()
        否则:
            target = date(year, month, day)
            if today > target:
                target = date(year + 1, month, day)
        return (target - today).days
    except:
        return "解析出错"

def send_message(to_user, token, config, weather_info, note):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    today = datetime.now().date()
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[datetime.now().isoweekday() % 7]
    
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days

    # 核心：精准构造数据包
    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "https://www.qweather.com/", # 点击可看天气详情
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_info[0], "color": get_color()},
            "temp": {"value": weather_info[1], "color": get_color()},
            "wind_dir": {"value": weather_info[2], "color": get_color()},
            "love_day": {"value": str(love_days), "color": "#FF1493"},
            "note_ch": {"value": note[0], "color": get_color()},
            "note_en": {"value": note[1], "color": get_color()}
        }
    }

    # 处理生日：确保 birthday1 和 birthday2 都能准确匹配
    for k, v in config.items():
        if k.startswith("birthday"):
            diff = get_birthday_days(v["birthday"], today)
            msg = f"今天{v['name']}生日啦！🎂" if diff == 0 else f"距离{v['name']}生日还有{diff}天"
            body["data"][k] = {"value": msg, "color": get_color()}

    res = post(url, json=body).json()
    print(f"发送至 {to_user}: {res}")

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        # 增强读取，过滤掉可能的非法字符
        content = "".join([line.split('#')[0] for line in f.readlines()])
        config = eval(content)

    token = get_access_token(config)
    weather = get_weather(config)
    
    # 获取每日一句
    try:
        cb = get("http://open.iciba.com/dsapi/").json()
        note = (config.get("note_ch") or cb["note"], config.get("note_en") or cb["content"])
    except:
        note = ("祝乖乖今天也开心！", "Have a nice day!")

    for user in config["user"]:
        send_message(user, token, config, weather, note)
