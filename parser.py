import json
from time import sleep

import requests
import sys

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

BASE_URL = "http://allrecipes.com/"


def str_to_min(ready_in_time_str):
    if "h" in ready_in_time_str:
        hour = int(ready_in_time_str.split("h")[0].strip())
        ready_in_time_str = ready_in_time_str.replace(str(hour), "").strip().replace("h", "").strip()
    else:
        hour = 0
    ready_in_time_str = ready_in_time_str.replace("m", "").strip()
    if not ready_in_time_str:
        min = 0
    else:
        min = int(ready_in_time_str)
    return hour * 60 + min


def parse_single_page(url_suff):
    res = requests.get(BASE_URL + url_suff)
    res_html = BeautifulSoup(res.text, "html.parser")
    # debugging
    # with open("examples/debug.html") as f:
    #     res = f.read()
    # res_html = BeautifulSoup(res, "html.parser")
    # title
    try:
        title = res_html.find("h1", itemprop="name").text
    except AttributeError:
        title = res_html.find("title").split("-").strip()
    # rating
    rating = float(res_html.find("meta", property="og:rating")["content"])
    # rating scale (max rating possible)
    rating_scale = float(res_html.find("meta", property="og:rating_scale")["content"])
    # total time (prep + cook)
    ready_in_time_str = res_html.find("span", {
        "class": "ready-in-time"
        }).text
    ready_in_time_min = str_to_min(ready_in_time_str.lower())
    ingredients = []
    for col in res_html.find_all("ul", id=lambda x: x and x.startswith("lst_ingredients_")):
        for ing in col.find_all("li"):
            ingredients.append(ing.text.replace("ADVERTISEMENT", "").strip())
    prep_time_str = res_html.find("time", itemprop="prepTime").text
    prep_time_min = str_to_min(prep_time_str.lower())
    cook_time_min = ready_in_time_min - prep_time_min
    directions = []
    for step in res_html.find_all("li", {
        "class": "step"
        }):
        if step.text:
            directions.append(step.text)

    ret = {
        "title":        title,
        "rating":       rating,
        "rating_scale": rating_scale,
        "rating_ratio": rating / rating_scale,
        "ready_time":   ready_in_time_min,
        "prep_time":    prep_time_min,
        "cook_time":    cook_time_min,
        "ingredients":  ingredients,
        "directions":   directions
    }
    # debug
    # with open("examples/debug.json", "w") as f:
    #     json.dump(ret, f)
    # print(ret)

    return ret


def get_recipes_from_page(page_num):
    res = requests.get(BASE_URL + "/recipes/?page=" + str(page_num))
    res_html = BeautifulSoup(res.text, "html.parser")
    recipes_list = []
    article_tags = res_html.find_all("article")
    for i in article_tags:
        try:
            if i.find("a")["href"].startswith("/recipe/"):
                recipes_list.append(i.find("a")["href"])
        except (KeyError, TypeError):
            pass
    return recipes_list


if __name__ == '__main__':
    page_num = sys.argv[1]
    page_end = sys.argv[2]
    for i in range(int(page_num), int(page_end)):
        recipes_list = get_recipes_from_page(i)
        if not recipes_list:
            break
        for page in recipes_list:
            ret = parse_single_page(page)
            with open("data", "a") as f:
                f.write(json.dumps(ret) + "\n")
            sleep(1)