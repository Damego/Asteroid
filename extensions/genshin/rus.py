rus_characters = {
    'Venti':'Венти',
    'Bennett':'Беннет',
    'Xiao':'Сяо',
    'Xingqiu':'Син Цю',
    'Zhongli':'Чжун Ли',
    'Ganyu':'Гань Юй',
    'Hu Tao':'Ху Тао',
    'Kazuha':'Кадзуха',
    'Jean':'Джин',
    'Diluc':'Дилюк',
    'Klee':'Кли',
    'Fischl':'Фишль',
    'Sucrose':'Сахароза',
    'Mona':'Мона',
    'Ningguang':'Нин Гуан',
    'Keqing':'Кэ Цин',
    'Ayaka':'Аяка',
    'Tartaglia':'Тарталья',
    'Diona':'Диона',
    'Albedo':'Альбедо',
    'Yoimiya':'Ёимия',
    'Eula':'Эола',
    'Yanfei':'Янь Фэй',
    'Kaeya':'Кэйя',
    'Barbara':'Барбара',
    'Razor':'Рейзор',
    'Noelle':'Ноэлль',
    'Beidou':'Бей Доу',
    'Xiangling':'Сян Лин',
    'Chongyun':'Чун Юнь',
    'Qiqi':'Ци Ци',
    'Rosaria':'Розария',
    'Amber':'Эмбер',
    'Lisa':'Лиза',
    'Xinyan':'Синь Янь',
    'Traveler':'Путешенственник'
}

rus_element = {
    'Anemo': '<:Element_Anemo:870989749534486538> Анемо',
    'Pyro': '<:Element_Pyro:870989754454396998> Пиро',
    'Hydro': '<:Element_Hydro:870989753649102909> Гидро',
    'Electro': '<:Element_Electro:870989752801837056> Электро',
    'Geo': '<:Element_Geo:870989753271603230> Гео',
    'Dendro': '<:Element_Dendro:870989751908446250> Дендро',
    'Cryo': '<:Element_Cryo:870989751312846868> Крио',
}

rus_region = {
    'Inazuma': 'Инадзума',
    'Liyue':'Ли Юэ',
    'Mondstadt':'Мондштадт'
}

rus_weapon_type = {
    'Sword': 'Одноручный меч',
    'Bow': 'Лук',
    'Claymore': 'Двуручный меч',
    'Catalyst': 'Катализатор',
    'Polearm': 'Копьё'

}

rus_artifact_type = {
    'flower':'Цветок',
    'feather':'Перо',
    'hourglass':'Часы',
    'goblet':'Кубок',
    'crown':'Корона',
}
def transform_abyss_name(old:str):
    floor, hall = old.split('-')
    new = f'Этаж {floor} Зал {hall}'
    return new