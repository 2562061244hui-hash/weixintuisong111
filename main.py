import random
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os

def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    return random.choice(get_colors(100))

def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        res = get(post_url).json()
        return res['access_token']
    except Exception as e:
        print(f"获取access_token失败: {e}")
        sys.exit(1)

def get_weather(config, region):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key = config["weather_key"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    response = get(region_url, headers=headers).json()
    if response["code"] != "200":
        print("城市查询失败，请检查地区名和Weather Key")
        sys.exit(1)
    location_id = response["location"][0]["id"]
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    res = get(weather_url, headers=headers).json()
    return res["now"]["text"], res["now"]["temp"] + "°C", res["now"]["windDir"]

def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_month, r_day = int(birthday.split("-")[1]), int(birthday.split("-")[2])
        try:
            target_date = ZhDate(year, r_month, r_day).to_datetime().date()
        except: return "日期错误"
    else:
        target_date = date(year, int(birthday.split("-")[1]), int(birthday.split("-")[2]))
    
    if today > target_date:
        if birthday_year[0] == "r":
            target_date = ZhDate(year + 1, r_month, r_day).to_datetime().date()
        else:
            target_date = date(year + 1, int(birthday.split("-")[1]), int(birthday.split("-")[2]))
    return (target_date - today).days

def send_message(to_user, access_token, config, weather_data, note):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    today = datetime.now().date()
    week = week_list[datetime.now().isoweekday() % 7]
    
    love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    love_days = (today - love_date).days

    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": f"{today} {week}", "color": get_color()},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_data[0], "color": get_color()},
            "temp": {"value": weather_data[1], "color": get_color()},
            "wind_dir": {"value": weather_data[2], "color": get_color()},
            "love_day": {"value": str(love_days), "color": get_color()},
            "note_en": {"value": note[1], "color": get_color()},
            "note_ch": {"value": note[0], "color": get_color()}
        }
    }

    for k, v in config.items():
        if k.startswith("birth"):
            diff = get_birthday(v["birthday"], today.year, today)
            msg = f"今天{v['name']}生日哦！" if diff == 0 else f"距离{v['name']}生日还有{diff}天"
            data["data"][k] = {"value": msg, "color": get_color()}

    print(f"推送至 {to_user}: {post(url, json=data).json()}")

if __name__ == "__main__":
    conf_path = "config.txt"
    if not os.path.exists(conf_path): sys.exit(1)
    
    # 增强版读取：自动忽略 # 注释行
    with open(conf_path, "r", encoding="utf-8") as f:
        lines = [line.split('#')[0] for line in f.readlines()]
        config = eval("".join(lines))

    token = get_access_token(config)
    w_info = get_weather(config, config["region"])
    
    # 获取词霸
    cb = get("http://open.iciba.com/dsapi/").json()
    note = (config.get("note_ch") or cb["note"], config.get("note_en") or cb["content"])

    for user in config["user"]:
        send_message(user, token, config, w_info, note)
