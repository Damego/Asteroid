rus_element = {
    'Anemo': '<:Element_Anemo:870989749534486538> `Анемо`',
    'Pyro': '<:Element_Pyro:870989754454396998> `Пиро`',
    'Hydro': '<:Element_Hydro:870989753649102909> `Гидро`',
    'Electro': '<:Element_Electro:870989752801837056> `Электро`',
    'Geo': '<:Element_Geo:870989753271603230> `Гео`',
    'Dendro': '<:Element_Dendro:870989751908446250> `Дендро`',
    'Cryo': '<:Element_Cryo:870989751312846868> `Крио`',
}

rus_region = {
    'Inazuma': 'Инадзума',
    'Liyue':'Ли Юэ',
    'Mondstadt':'Мондштадт',
    'Dragonspine':'Драконий Хребет'
}

rus_artifact_type = {
    'flower':'<:Icon_Flower_of_Life:871372154179059742> Цветок',
    'feather':'<:Icon_Plume_of_Death:871372154510397470> Перо',
    'hourglass':'<:Icon_Sands_of_Eon:871372154845933568> Часы',
    'goblet':'<:Icon_Goblet_of_Eonothem:871372154346827776> Кубок',
    'crown':'<:Icon_Circlet_of_Logos:871372154212605962> Корона',
}

def transform_abyss_name(old_name:str):
    floor, hall = old_name.split('-')
    new_name = f'Этаж {floor} Зал {hall}'
    return new_name