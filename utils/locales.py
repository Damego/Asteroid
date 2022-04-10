import json
from os import listdir


def get_content(content_type: str, lang: str):
    if lang == "English":
        lang = "en-US"
    elif lang == "Russian":
        lang = "ru"
    return locales[lang][content_type]


def load_localization():
    global locales, locales_list
    for locale_filename in listdir("./locales"):
        locale = locale_filename.replace(".json", "")
        locales_list.append(locale)
        with open(f"./locales/{locale_filename}", encoding="UTF-8") as locale_file:
            locales = locales | {locale: json.load(locale_file)}


locales = {}
locales_list = []
