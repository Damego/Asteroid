import json
from os import listdir

locales = {}
locales_list = set()


def get_content(content_type: str, lang: str):
    if lang == "English":
        lang = "en-US"
    elif lang == "Russian":
        lang = "ru"

    if lang not in locales:
        return locales["en-US"][content_type]
    return locales[lang][content_type]


def load_localization():
    global locales, locales_list
    locales = {}
    locales_list = set()
    not_loaded = []

    for locale_filename in listdir("./locales"):
        locale = locale_filename.replace(".json", "")
        with open(f"./locales/{locale_filename}", encoding="UTF-8") as locale_file:
            try:
                locales = locales | {locale: json.load(locale_file)}
                locales_list.add(locale)
            except json.decoder.JSONDecodeError as exception:
                print(f"Cannot load {locale_filename}. Exception: {exception}")
                not_loaded.append(locale_filename)

    return not_loaded
