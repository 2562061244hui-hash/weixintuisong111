import random
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys

def get_color():
    return random.choice(["#FF69B4", "#1E90FF", "#32CD32", "#FFA500", "#9370DB"])

def get_access_token(config):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config['app_id']}&secret={config['app_secret']}"
    return get(url).json().get('access_token')

def get_weather(config):
    headers = {'User-Agent': 'Mozilla/5.0'}
    key, region = config["weather_key"], config["region"]
    try:
        r_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
        city_id = get(r_url, headers=headers).json()["location"][0]["id"]
        w_url = f"https://devapi.qweather.com/v7/weather/now?location={city_id}&key={key}"
        res = get(w_url, headers=headers).json()["now"]
        return res["text"], res["temp"] + "°"
    except: return "未知", "N/A"

def get_birthday(b_str, today):
    year = today.year
    is_lunar = b_str.startswith("r")
    clean_date = b_str.replace("r", "")
    try:
        m, d = map(int, clean_date.split("-")[1:3])
        target = ZhDate(year, m, d).to_datetime().date() if is_lunar else date(year, m, d)
        if today > target:
            target = ZhDate(year + 1, m, d).to_datetime().date() if is_lunar else date(year + 1, m, d)
        return (target - today).days
    except: return None

def send_message(to_user, token, config, weather_info):
    today = datetime.now().date()
    love_days = (today - datetime.strptime(config["love_date"], "%Y-%m-%d").date()).days
    
    # 极简生日拼接
    memo_list = []
    for k, v in config.items():
        if k.startswith("birthday"):
            diff = get_birthday(v["birthday"], today)
            if diff is not None:
                memo_list.append(f"{v['name']}{'诞辰!' if diff==0 else '生还有'+str(diff)+'天'}")
    memo_text = " / ".join(memo_list) if memo_list else "今天也要开心呀 ❤️"

    # 极简金句
    try:
        note = config.get("note_ch") or get("http://open.iciba.com/dsapi/").json()["note"]
    except: note = "每天都要想我哦！"

    body = {
        "touser": to_user,
        "template_id": config["template_id"],
        "data": {
            "date": {"value": f"{today.month}-{today.day}", "color": get_color()},
            "love_day": {"value": str(love_days), "color": "#FF1493"},
            "region": {"value": config["region"], "color": get_color()},
            "weather": {"value": weather_info[0], "color": get_color()},
            "temp": {"value": weather_info[1], "color": get_color()},
            "memo": {"value": memo_text, "color": get_color()},
            "note": {"value": note[:40], "color": get_color()} # 限制40字，防止截断
        }
    }
    post(f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}", json=body)

if __name__ == "__main__":
    with open("config.txt", "r", encoding="utf-8") as f:
        config = eval("".join([line.split('#')[0] for line in f.readlines()]))
    token = get_access_token(config)
    weather = get_weather(config)
    for user in config["user"]:
        send_message(user, token, config, weather)
