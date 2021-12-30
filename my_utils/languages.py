def get_content(content_type: str, lang: str):
    return LANGUAGES[lang][content_type]


LANGUAGES = {
    'ru': {
        'ERRORS_DESCRIPTIONS': {
            'COG_DISABLED': 'Эта команда отключена на этом сервере!',
            'COMMAND_DISABLED': 'Эта команда или группа команд была отключена на этом сервере!',
            'TAG_NOT_FOUND': 'Тег не найден!',
            'FORBIDDEN_TAG': 'Этот тег нельзя использовать!',
            'NOT_TAG_OWNER': 'Вы не владелец тега!',
            'UID_NOT_BINDED': 'У вас не привязан UID!',
            'GI_ACCOUNT_NOT_FOUND': 'Аккаунт с таким UID не найден!',
            'GI_DATA_NOT_PUBLIC': 'Профиль закрыт! Откройте профиль на [сайте]('
                                  'https://www.hoyolab.com/genshin/accountCenter/gameRecord)',
            'NOT_CONNECTED_TO_VOICE': 'You not connected to voice channel!',
            'NOT_BOT_OWNER': 'Это команда доступна только владельцу бота!',
            'BOT_MISS_PERMS': '**У бота недостаточно прав!**\nНеобходимые права: ',
            'MISS_PERMS': '**У вас недостаточно прав!**\nНеобходимые права:',
            'CHECK_FAILURE': 'Вы не можете использовать эту команду!',
            'OTHER_ERRORS_TITLE': '❌ Упс... Произошла непредвиденная ошибка!',
            'OTHER_ERRORS_DESCRIPTION': 'Этот баг был отправлен создателю\n *Ошибка:* ```\n{error}\n```',
            'BOT_DONT_HAVE_PERMS': '**У бота недостаточно прав чтобы сделать это!**\nТребуется:',
            'DONT_HAVE_PERMS': '**У вас недостаточно прав для использования этой команды!**\nТребуется:',
            'FORBIDDEN': 'У бота недостаточно прав чтобы сделать это',
            'BAD_ARGUMENT': 'Вы ввели неверно один из аргументов!'
        },
        'FUNC_RANDOM_NUMBER_OUT_CONTENT': 'Рандомное число: `{}`',
        'FUNC_MEMBER_INFO': {
            'MEMBER_STATUS': {
                'online': '<:s_online:850792217031082051> В сети',
                'dnd': '<:dnd:850792216943525936> Не беспокоить',
                'idle': '<:s_afk:850792216732368937> Отошёл',
                'offline': '<:s_offline:850792217262030969> Не в сети'
            },
            'ABOUT_TITLE': 'Информация о {}',
            'GENERAL_INFO_TITLE': 'Общая информация:',
            'FULL_NAME_TEXT': 'Полное имя',
            'BADGES_TEXT': 'Значки:',
            'DISCORD_REGISTRATION_TEXT': 'Дата регистрации в Discord:',
            'JOINED_ON_SERVER_TEXT': 'Дата присоединения на сервер:',
            'CURRENT_STATUS_TEXT': 'Текущий статус:',
            'TOP_ROLE_TEXT': 'Высшая роль:',
            'ROLES_TEXT': 'Роли:',
            'LEVELING': {
                'CURRENT_LEVEL_TEXT': '<:level:863677232239869964> **Уровень:** `{level}`',
                'CURRENT_EXP_TEXT': '<:exp:863672576941490176> **Опыт:** `{exp}/{exp_to_next_level}` Всего: `{exp_amount}`',
                'LEVELING_INFO_TITLE_TEXT': 'Уровневая информация',
                'TOTAL_VOICE_TIME': '<:voice_time:863674908969926656> **Время в голосом канале:** `{voice_time}` минут'
            }
        },
        'FUNC_PING': 'Задержка бота `{}` мс',
        'INVITE_COMMAND': {
            'INVITE_BUTTON_NO_PERMS': 'Без разрешений',
            'INVITE_BUTTON_ADMIN': 'Администратор',
            'INVITE_BUTTON_RECOMMENDED': 'Рекомендуемый',
            'CLICK_TO_INVITE_TEXT': 'Нажмите на кнопку, чтобы пригласить бота',
        },
        'FUNC_ACTIVITIES': {
            'NOT_CONNECTED_TO_CHANNEL_TEXT': 'Вы не подключены к голосовому каналу!',
            'WRONG_CHANNEL_TEXT': 'Вы выбрали неверный канал! Выберите голосовой!',
            'JOIN_TEXT': '**Присоединиться**',
            'REQUESTED_BY_TEXT': 'Запрошено {}'
        },
        'GAMES_NAMES': {
            'RPS': 'Камень Ножницы бумага',
            'TTT': 'Крестики Нолики'
        },
        'FUNC_INVITE_TO_GAME': {
            'SELF_INVITE': 'Вы не можете пригласить себя!',
            'BOT_INVITE': 'Вы не можете пригласить бота!',
            'INVITE_MESSAGE_CONTENT': '{}! {} приглашает тебя в игру {}',
            'BUTTON_AGREE': 'Согласиться',
            'BUTTON_DECLINE': 'Отказаться',
            'AGREE_MESSAGE_CONTENT': 'Вы приняли приглашение!',
            'DECLINE_MESSAGE_CONTENT': '{} отказался от игры!',
            'TIMEOUT_MESSAGE_CONTENT': 'От {} нет ответа!'
        },
        'GAME_RPS': {
            'RESULTS_TITLE': '`          ИТОГИ ИГРЫ            `',
            'RESULTS_TEXT': '' \
                            '**Игроки:** {} и {} \n' \
                            '**Количество сыгранных игр:** {} \n' \
                            '**Счёт:** {}:{} \n' \
                            '**Победитель:** {}',
            'RESULTS_GAME_NAME': '**Название игры: Камень ножницы бумага**',
            'RESULTS_TIE': 'Ничья',
            'MADE_MOVE_TEXT': 'Вы сделали свой ход',
            'PLAYERS_TEXT': '**{}** VS **{}**',
            'CURRENT_SCORE_TEXT': '**Счёт:** {}:{}\n' \
                                  '**Игра:** {}/{}',
        },
        'GAME_TTT': {
            'GAME_NAME': 'Крестики Нолики',
            'RESULTS_TITLE': '`          ИТОГИ ИГРЫ            `',
            'RESULTS_GAME_NAME': '**Игра: Крестики Нолики**',
            'RESULTS_TEXT': '**Игроки: {player1} И {player2}**\n**Победитель:** {winner}',
            'RESULTS_TIE': 'Ничья',
        },
        'FUNC_MODERATION_CHANGE_NICK_TEXT': 'Был изменён ник {} на `{}`',
        'FUNC_MODERATION_MUTE_MEMBER': {
            'CANNOT_MUTE_BOT_TEXT': 'Вы не можете замутить бота!',
            'WAS_MUTED_TEXT': '{} был отправлен в мут!',
            'TIME_TEXT': '**Время**: {amount} {time_format}\n',
            'REASON_TEXT': '**Причина**: {reason}',
            'MUTED_ROLE_CREATED_TEXT': 'Роль для мута `role_name` была создана!'
        },
        'FUNC_MODERATION_BAN_MEMBER': {
            'CANNOT_BAN_BOT_TEXT': 'Вы не можете забанить бота!',
            'WAS_BANNED_TEXT': '{member} был забанен!',
            'REASON_TEXT': '**Причина**: {reason}',
            'SERVER': '\n**Сервер:** {guild}'
        },
        'FUNC_MODERATION_KICK_MEMBER': {
            'CANNOT_KICK_BOT_TEXT': 'Вы не можете кикнуть бота!',
            'WAS_KICKED_TEXT': '{member} был кикнут!',
            'REASON_TEXT': '**Причина**: {reason}',
            'SERVER': '\n**Сервер:** {guild}'
        },
        'FUNC_MODERATION_CLEAR_MESSAGES': 'Успешно удалено `{}` сообщений!',
        'PUBLIC_TAGS_COMMAND': {
            'TAGS_PUBLIC': 'Теги теперь доступны всем!',
            'TAGS_FOR_ADMINS': 'Теги теперь могут создавать только те, у кого есть право `Управлять сервером`!'
        },
        'EMBED_TAG_CONTROL': {
            'NOT_SUPPORTED_TAG_TYPE': 'Этот тег не поддерживается!',
            'EDIT_TAG_BUTTON': 'Редактировать',
            'REMOVE_TAG_BUTTON': 'Удалить',
            'EXIT_BUTTON': 'Выйти',
            'SET_TITLE_BUTTON': 'Заголовок',
            'SET_DESCRIPTION_BUTTON': 'Описание',
            'GET_RAW_DESCRIPTION_BUTTON': 'Исходник',
            'SAVE_TAG_BUTTON': 'Сохранить',
            'TAG_TITLE_TEXT': 'Заголовок Тега',
            'TAG_DESCRIPTION_TEXT': 'Описание Тега',
            'INPUT_TEXT': 'Введите',
            'SAVED_TAG_TEXT': '**Сохранено!**',
            'REMOVED_TAG_TEXT': '**Тег удалён!**'
        },
        'FUNC_TAG_LIST': {
            'TAGS_LIST_TEXT': 'Список тегов в {server}',
            'NO_TAGS_TEXT': 'Список пуст!'
        },
        'TAG_ADD_COMMAND': {
            'TAG_ALREADY_EXISTS_TEXT': 'Этот тег уже существует!',
            'TAG_CREATED_TEXT': 'Тег `{tag_name}` успешно создан!'
        },
        'TAG_REMOVE_COMMAND': {
            'TAG_REMOVED_TEXT': 'Тег `{tag_name}` успешно удалён!'
        },
        'TAG_RENAME_TAG': {
            'TAG_RENAMED_TEXT': 'Тег `{tag_name}` переименован в `{new_tag_name}`!'
        },
        'MUSIC_PLAY_COMMAND': {
            'ADDED_IN_QUEUE_TEXT': '`{}` Было добавлено о очередь',
            'NOT_CONNECTED_TO_VOICE': 'Подключитесь к голосовому каналу с ботом!',
            'PAUSE_BUTTON': 'Пауза',
            'RESUME_BUTTON': 'Продолжить',
            'STOP_BUTTON': 'Стоп',
            'SKIP_BUTTON': 'Пропустить',
            'TOGGLE_OFF_BUTTON': 'Выкл. повтор',
            'TOGGLE_ON_BUTTON': 'Вкл. повтор',
            'PLAYING_TEXT': 'Сейчас играет',
            'NAME_TEXT': 'Название:',
            'DURATION_TEXT': 'Продолжительность:',
            'LIVE_TEXT': 'Прямая трансляция',
            'WHO_ADDED_TEXT': 'Добавлено {}',
            'SUCCESSFULLY': 'Успешно!'
        },
        'FUNC_RANDOM_ITEMS': {
            'ITEMS_LIST': [
                'Успокоительное', 'Термометр', 'Фотокамера', 'Направленный микрофон',
                'Свеча', 'Благовоние', 'Зажигалка', 'Распятие', 'Соль',
                'Штатив',
                'Датчик ЭМП', 'Радиоприёмник', 'Блокнот', 'Лазерный проектор', 'Видеокамера',
                'Слабый фонарик', 'УФ-фонарик', 'Сильный фонарик',
                'Датчик движения', 'Неоновая палочка', 'Датчик звука',
                'Камера с креплением на голову'
            ],
            'SELECT_BUTTON': 'Выборка',
            'EXCEPTION_BUTTON': 'Исключение',
            'SELECT_ITEMS_TEXT': 'Выберите предметы',
            'START_RANDOM_BUTTON': 'Рандом!',
            'EXIT_BUTTON': 'Выйти',
            'EMBED_TITLE': 'Рандомные предметы!',
            'SECOND_MESSAGE_CONTENT': 'Здесь будет появляться предмет',
            'SELECTED_ITEMS_TEXT': '**Выбранные предметы: **\n',
        },
        'GENSHIN_BIND_COMMAND': 'Вы привязали UID',
        'GENSHIN_STATISTICS_COMMAND': {
            'EMBED_WORLD_EXPLORATION_TITLE': 'Genshin Impact. Статистика мира',
            'EXPLORED_TEXT': 'Исследовано',
            'FROSTBEARING_TREE_LEVEL_TEXT': '\nУровень Дерева Вечной Мерзлоты: `{level}`',
            'SACRED_SAKURA_LEVEL_TEXT': '\nУровень Благосклонности сакуры: `{level}`',
            'REPUTATION_LEVEL_TEXT': '\nУровень репутации: `{level}`',
            'ANEMOCULUS': 'Анемокулов',
            'GEOCULUS': 'Геокулов',
            'ELECTROCULUS': 'Электрокулов',
            'COLLECTED_OCULUS_TEXT': 'Собрано окулов',
            'COMMON_CHEST': 'Обычных',
            'EXQUISITE_CHEST': 'Богатых',
            'PRECIOUS_CHEST': 'Драгоценных',
            'LUXURIOUS_CHEST': 'Роскошных',
            'CHESTS_OPENED': 'Открыто сундуков',
            'UNLOCKED_TELEPORTS': 'Открыто телепортов',
            'UNLOCKED_DOMAINS': 'Открыто подземелий',
            'MISC_INFO': 'Остальное'
        },
        'GENSHIN_CHARACTERS_LIST_COMMAND': {
            'EMBED_GENSHIN_CHARACTERS_LIST_TITLE': 'Genshin Impact. Персонажи',
            'CHARACTER_LEVEL': 'Уровень',
            'CHARACTER_CONSTELLATION': 'Созвездие',
            'CHARACTER_VISION': 'Глаз бога',
            'CHARACTER_WEAPON': 'Оружие',
        },
        'GENSHIN_CHARACTERS_COMMAND': {
            'INFORMATION_TEXT': '**Информация**',
            'CHARACTER_LEVEL': 'Уровень',
            'CHARACTER_CONSTELLATION': 'Созвездие',
            'CHARACTER_VISION': 'Глаз бога',
            'CHARACTER_FRIENDSHIP': 'Уровень дружбы',
            'WEAPON_TEXT': '**Оружие**',
            'WEAPON_NAME': 'Название',
            'WEAPON_RARITY': 'Редкость',
            'WEAPON_TYPE': 'Тип',
            'WEAPON_LEVEL': 'Уровень',
            'WEAPON_ASCENSION_LEVEL': 'Уровень восхождения',
            'WEAPON_REFINEMENT_LEVEL': 'Уровень пробуждения',
            'ARTIFACTS_TEXT': '**Артефакты**',
            'ARTIFACT_NAME': 'Название',
            'ARTIFACT_RARITY': 'Редкость',
            'ARTIFACT_LEVEL': 'Уровень',
            'GENSHIN_CHARACTER_VISION': {
                'Anemo': '<:Element_Anemo:870989749534486538> `Анемо`',
                'Pyro': '<:Element_Pyro:870989754454396998> `Пиро`',
                'Hydro': '<:Element_Hydro:870989753649102909> `Гидро`',
                'Electro': '<:Element_Electro:870989752801837056> `Электро`',
                'Geo': '<:Element_Geo:870989753271603230> `Гео`',
                'Dendro': '<:Element_Dendro:870989751908446250> `Дендро`',
                'Cryo': '<:Element_Cryo:870989751312846868> `Крио`',
            },
            'GENSHIN_ARTIFACT_TYPE': {
                'flower': '<:Icon_Flower_of_Life:871372154179059742> Цветок',
                'feather': '<:Icon_Plume_of_Death:871372154510397470> Перо',
                'hourglass': '<:Icon_Sands_of_Eon:871372154845933568> Часы',
                'goblet': '<:Icon_Goblet_of_Eonothem:871372154346827776> Кубок',
                'crown': '<:Icon_Circlet_of_Logos:871372154212605962> Корона',
            }
        },
        'GENSHIN_INFO_COMMAND': {
            'NICKNAME_TEXT': 'Ник в игре',
            'ADVENTURE_RANK_TEXT': 'Ранг Приключений',
            'ACHIEVEMENTS_TEXT': 'Достижений',
            'CHARACTERS_TEXT': 'Персонажей',
            'SPIRAL_ABYSS_TEXT': 'Витая Бездна',
            'PLAYER_INFO_TEXT': 'Информация об игроке',
        },
        'SET_EMBED_COLOR_COMMAND': {
            'WRONG_COLOR': 'Неверный формат цвета!',
            'SUCCESSFULLY_CHANGED': 'Цвет сообщений успешно изменён!'
        },
        'LEVELS': {
            'FUNC_UPDATE_MEMBER': {
                'NOTIFY_GUILD_CHANNEL': '{member} получил `{level}-й` уровень и повышение до {role}',
                'NOTIFY_DM': 'Вы получили `{level}-й` уровень и повышение до {role}'
            },
            'FUNC_TOP_MEMBERS': {
                'TITLES': '**ID | Участник | Текущий уровень**\n',
                'TOP_MEMBERS_TEXT': 'Топ участников по уровню',
                'REQUESTED_BY_TEXT': 'Запрошено'
            }
        },
        'HELP_COMMAND': {
            'INFORMATION_TEXT': 'Информация',
            'INFORMATION_CONTENT_TEXT': '```Подсказка: [обязательный аргумент] (необязательный аргумент)```',
            'REQUIRED_BY_TEXT': 'Запрошено {user}',
            'PLUGINS_TEXT': 'Плагины',
            'SELECT_MODULE_TEXT': 'Выберите плагин'
        },
        'STARBOARD_FUNCTIONS': {
            'CHANNEL_WAS_SETUP_TEXT': 'Канал был установлен!',
            'LIMIT_WAS_SETUP_TEXT': 'Лимит звёзд был установлен до `{limit}`!',
            'STARBOARD_NOT_SETUP_TEXT': 'Канал или лимит звёзд не были установлены!',
            'STARBOARD_ENABLED_TEXT': 'Starboard был `включен`!',
            'STARBOARD_DISABLED_TEXT': 'Starboard был `выключен`!',
            'JUMP_TO_ORIGINAL_MESSAGE_TEXT': 'Перейти к сообщению!',
            'BLACKLIST_NO_OPTIONS_TEXT': 'Должно быть что-то из `member`, `role`, `channel`',
            'EMPTY_BLACKLIST_TEXT': 'Чёрный список пуст!',
            'BLACKLIST_ADDED_TEXT': 'Добавлено',
            'BLACKLIST_REMOVED_TEXT': 'Удалено',
            'BLACKLIST_TEXT': '⭐Starboard. Чёрный список',
            'MEMBERS': 'Участники',
            'CHANNELS': 'Каналы',
            'ROLES': 'Роли'
        },
        'AUTOROLE_DROPDOWN': {
            'ADDED_ROLES_TEXT': 'Добавлено: ',
            'REMOVED_ROLES_TEXT': '\nУдалено: ',
            'NO_OPTIONS_TEXT': 'Нет опций',
            'CREATED_DROPDOWN_TEXT': 'Меню создано!',
            'MESSAGE_WITHOUT_DROPDOWN_TEXT': 'Сообщение не имеет меню!',
            'OPTIONS_OVERKILL_TEXT': 'Вы не можете добавить больше 25 опций в меню1',
            'SELECT_ROLE_TEXT': 'Выберите роль',
            'ROLE_ADDED_TEXT': 'Роль добавлена!',
            'OPTION_NOT_FOUND_TEXT': 'Не удалось найти опцию с таким именем!',
            'OPTIONS_LESS_THAN_1_TEXT': 'Опций в меню не может быть меньше 1',
            'ROLE_REMOVED_TEXT': 'Роль удалена!',
            'DROPDOWN_ENABLED_TEXT': 'Меню включено!',
            'DROPDOWN_DISABLED_TEXT': 'Меню выключено!',
            'DROPDOWN_SAVED_TEXT': 'Сохранено!',
            'NOT_SAVED_DROPDOWNS': 'Нет сохранённих меню!',
            'DROPDOWN_NOT_FOUND': 'Нет меню с таким именем!',
            'DROPDOWN_LOADED_TEXT': 'Меню загружено!',
            'DROPDOWN_LIST': 'Список меню с ролями'
        },
        'AUTOROLE_ON_JOIN': {
            'ROLE_ADDED_TEXT': 'Роль {role} Добавлена!',
            'ROLE_REMOVED_TEXT': 'Роль {role} Удалена!'
        },
        'TIME_FORMATS': {
            'с': 'сек.',
            'м': 'мин.',
            'ч': 'час.',
            'д': 'дн.',
            's': 'сек.',
            'm': 'мин.',
            'h': 'час.',
            'd': 'дн.',
        },
        'COMMAND_CONTROL': {
            'COMMAND_DISABLED': 'Команда `{command_name}` была выключена!',
            'COMMAND_ENABLED': 'Команда `{command_name}` была включена!'
        }
    },
    'en': {
        'ERRORS_DESCRIPTIONS': {
            'COG_DISABLED': 'This command disabled on this server!',
            'COMMAND_DISABLED': 'This command or group of commands was disabled on this server!',
            'TAG_NOT_FOUND': 'Tag not found!',
            'FORBIDDEN_TAG': 'This tag cannot be used!',
            'NOT_TAG_OWNER': 'You not owner of this tag!',
            'UID_NOT_BINDED': 'You didn\'t tie UID!',
            'GI_ACCOUNT_NOT_FOUND': 'Account with this UID not found!',
            'GI_DATA_NOT_PUBLIC': 'Profile is private! Open profile on [site](https://www.hoyolab.com/genshin/accountCenter/gameRecord)',
            'NOT_CONNECTED_TO_VOICE': 'You not connected to voice channel!',
            'NOT_BOT_OWNER': 'Only owner can use this command!',
            'BOT_MISS_PERMS': 'Bot don\'t have permission for this!**\nRequired permissions: ',
            'MISS_PERMS': 'You don\'t have permission for this!**\nRequired permissions:',
            'CHECK_FAILURE': 'You can\'t use this command!',
            'OTHER_ERRORS_TITLE': '❌ Oops... An unexpected error occurred!',
            'OTHER_ERRORS_DESCRIPTION': 'This bug was sent to owner\n' \
                                        '*Error:* \n' \
                                        '```python ' \
                                        '{error}' \
                                        ' ```',
            'BOT_DONT_HAVE_PERMS': '**Bot don\'t have permission for this!**\nRequired permissions:',
            'DONT_HAVE_PERMS': '**You don\'t have permission for this!**\nRequired permissions:',
            'FORBIDDEN': 'Bot doesn\'t have permission for this!',
            'BAD_ARGUMENT': 'One of arguments is wrong!',
        },
        'FUNC_RANDOM_NUMBER_OUT_CONTENT': 'Random number is `{}`',
        'FUNC_MEMBER_INFO': {
            'MEMBER_STATUS': {
                'online': '<:s_online:850792217031082051> Online',
                'dnd': '<:dnd:850792216943525936> Do not disturb',
                'idle': '<:s_afk:850792216732368937> Idle',
                'offline': '<:s_offline:850792217262030969> Offline'
            },
            'ABOUT_TITLE': 'Information about {}',
            'GENERAL_INFO_TITLE': 'General information:',
            'FULL_NAME_TEXT': 'Full name',
            'BADGES_TEXT': 'Badges:',
            'DISCORD_REGISTRATION_TEXT': 'Date of registration in Discord:',
            'JOINED_ON_SERVER_TEXT': 'Date of joined in server:',
            'CURRENT_STATUS_TEXT': 'Current status:',
            'TOP_ROLE_TEXT': 'Top role:',
            'ROLES_TEXT': 'Roles:',
            'LEVELING': {
                'CURRENT_LEVEL_TEXT': '<:level:863677232239869964> **Level:** `{level}`',
                'CURRENT_EXP_TEXT': '<:exp:863672576941490176> **Exp:** `{exp}/{exp_to_next_level}` Total: `{exp_amount}`',
                'LEVELING_INFO_TITLE_TEXT': 'Level Information',
                'TOTAL_VOICE_TIME': '<:voice_time:863674908969926656> **Time in voice channel:** `{voice_time}` minutes'
            }
        },
        'INVITE_COMMAND': {
            'INVITE_BUTTON_NO_PERMS': 'Without permissions',
            'INVITE_BUTTON_ADMIN': 'Administrator',
            'INVITE_BUTTON_RECOMMENDED': 'Recommenend',
            'CLICK_TO_INVITE_TEXT': 'Click on button to invite bot!',
        },
        'FUNC_PING': 'Bot latency is `{}` ms',
        'FUNC_ACTIVITIES': {
            'NOT_CONNECTED_TO_CHANNEL_TEXT': 'You not connected to voice channel!',
            'WRONG_CHANNEL_TEXT': 'You selected wrong channel! Select voice channel!',
            'JOIN_TEXT': '**JOIN**',
            'REQUESTED_BY_TEXT': 'Requested by {}'
        },
        'GAMES_NAMES': {
            'RPS': 'Rock Paper Scissors',
            'TTT': 'Tic Tac Toe'
        },
        'FUNC_INVITE_TO_GAME': {
            'SELF_INVITE': 'You can not invite yourself!',
            'BOT_INVITE': 'You can not invite Bot!',
            'INVITE_MESSAGE_CONTENT': '{}! {} invited you in game {}',
            'BUTTON_AGREE': 'Agree',
            'BUTTON_DECLINE': 'Decline',
            'AGREE_MESSAGE_CONTENT': 'You accept invite!',
            'DECLINE_MESSAGE_CONTENT': '{} refused to game!',
            'TIMEOUT_MESSAGE_CONTENT': 'no response from {}!'
        },
        'GAME_RPS': {
            'RESULTS_TITLE': '`          Results            `',
            'RESULTS_TEXT': '' \
                            '**Players:** {} vs. {} \n' \
                            '**Rounds played:** {} \n' \
                            '**Score:** {}:{} \n' \
                            '**Winner:** {}',
            'RESULTS_GAME_NAME': '**Game name: Rock Paper Scissors**',
            'RESULTS_TIE': 'Draw',
            'MADE_MOVE_TEXT': 'You made move',
            'PLAYERS_TEXT': '**{}** vs. **{}**',
            'CURRENT_SCORE_TEXT': '**Score:** {}:{}\n**Match:** {}/{}',
        },
        'GAME_TTT': {
            'GAME_NAME': 'Tic Tac Toe',
            'RESULTS_TITLE': '`          Results            `',
            'RESULTS_GAME_NAME': '**Name: Tic Tac Toe**',
            'RESULTS_TEXT': '**Players: {player1} and {player2}**\n**Winner:** {winner}',
            'RESULTS_TIE': 'Draw',
        },
        'FUNC_MODERATION_CHANGE_NICK_TEXT': 'Nick of {} was changed to `{}`',
        'FUNC_MODERATION_MUTE_MEMBER': {
            'CANNOT_MUTE_BOT_TEXT': 'You can\'t mute bot!',
            'WAS_MUTED_TEXT': '{} was muted!',
            'TIME_TEXT': '**Timeout**: {amount} {time_format}\n',
            'REASON_TEXT': '**Reason**: {reason}',
            'MUTED_ROLE_CREATED_TEXT': 'Muted role with name `{role_name}` created!'
        },
        'FUNC_MODERATION_BAN_MEMBER': {
            'CANNOT_BAN_BOT_TEXT': 'You can\'t ban bot!',
            'WAS_BANNED_TEXT': '{member} was banned!',
            'REASON_TEXT': '**Reason**: {reason}',
            'SERVER': '\n**Server:** {guild}'
        },
        'FUNC_MODERATION_KICK_MEMBER': {
            'CANNOT_KICK_BOT_TEXT': 'You can\'t kick bot!',
            'WAS_KICKED_TEXT': '{member} was kicked!',
            'REASON_TEXT': '**Reason**: {reason}',
            'SERVER': '\n**Server:** {guild}'
        },
        'FUNC_MODERATION_CLEAR_MESSAGES': 'Successfully deleted `{}` messages!',
        'PUBLIC_TAGS_COMMAND': {
            'TAGS_PUBLIC': 'Tags for now public!',
            'TAGS_FOR_ADMINS': 'For now tags only for roles with `Manage Server` permission!'
        },
        'EMBED_TAG_CONTROL': {
            'NOT_SUPPORTED_TAG_TYPE': 'This tag not supported!',
            'EDIT_TAG_BUTTON': 'Edit',
            'REMOVE_TAG_BUTTON': 'Delete',
            'EXIT_BUTTON': 'Exit',
            'SET_TITLE_BUTTON': 'Title',
            'SET_DESCRIPTION_BUTTON': 'Description',
            'GET_RAW_DESCRIPTION_BUTTON': 'Get raw',
            'SAVE_TAG_BUTTON': 'Save',
            'TAG_TITLE_TEXT': 'Tag title',
            'TAG_DESCRIPTION_TEXT': 'Tag description',
            'INPUT_TEXT': 'Input',
            'SAVED_TAG_TEXT': '**Saved!**',
            'REMOVED_TAG_TEXT': '**Tag was deleted!**'
        },
        'TAG_ADD_COMMAND': {
            'TAG_ALREADY_EXISTS_TEXT': 'This tag already exists!',
            'TAG_CREATED_TEXT': 'Tag `{tag_name}` successfully created!'
        },
        'TAG_REMOVE_COMMAND': {
            'TAG_REMOVED_TEXT': 'Tag `{tag_name}` successfully removed!'
        },
        'TAG_RENAME_TAG': {
            'TAG_RENAMED_TEXT': 'Tag `{tag_name}` renamed to `{new_tag_name}`!'
        },
        'FUNC_TAG_LIST': {
            'TAGS_LIST_TEXT': 'Tags list on {server}',
            'NO_TAGS_TEXT': 'No tags in this server!'
        },
        'MUSIC_PLAY_COMMAND': {
            'ADDED_IN_QUEUE_TEXT': '`{}` was added in queue',
            'NOT_CONNECTED_TO_VOICE': 'Connect to voice channel with a bot',
            'PAUSE_BUTTON': 'Pause',
            'RESUME_BUTTON': 'Resume',
            'STOP_BUTTON': 'Stop',
            'SKIP_BUTTON': 'Skip',
            'TOGGLE_OFF_BUTTON': 'Disable repeat',
            'TOGGLE_ON_BUTTON': 'Enable repeat',
            'PLAYING_TEXT': 'Now playing',
            'NAME_TEXT': 'Name:',
            'DURATION_TEXT': 'Duration:',
            'LIVE_TEXT': 'Live',
            'WHO_ADDED_TEXT': 'Added {}',
            'SUCCESSFULLY': 'Successfully!'
        },
        'FUNC_RANDOM_ITEMS': {
            'ITEMS_LIST': [
                'Sanity Pills', 'Thermometer', 'Photo Camera', 'Parabolic Microphone',
                'Candle', 'Smudge Sticks', 'Lighter', 'Crucifix', 'Salt Shaker',
                'Tripod',
                'EMF Reader', 'Spirit Box', 'Ghost Writing Book', 'D.O.T.S Projector', 'Video Camera',
                'Flashlight', 'UV Flashlight', 'Strong Flashlight',
                'Motion Sensor', 'Glow Stick', 'Sound Sensor',
                'Head Mounted Camera'
            ],
            'SELECT_BUTTON': 'Select',
            'EXCEPTION_BUTTON': 'Except',
            'SELECT_ITEMS_TEXT': 'Select items',
            'START_RANDOM_BUTTON': 'Random!',
            'EXIT_BUTTON': 'Exit',
            'EMBED_TITLE': 'Random items!',
            'SECOND_MESSAGE_CONTENT': 'Here will be appear item',
            'SELECTED_ITEMS_TEXT': '**Selected items: **\n',
        },
        'GENSHIN_BIND_COMMAND': 'You binded UID',
        'GENSHIN_STATISTICS_COMMAND': {
            'EMBED_WORLD_EXPLORATION_TITLE': 'Genshin Impact. World exploration',
            'EXPLORED_TEXT': 'Explored',
            'FROSTBEARING_TREE_LEVEL_TEXT': '\nLevel of Frostbearing Tree: `{level}`',
            'SACRED_SAKURA_LEVEL_TEXT': '\nLevel of Sacred Sakura\'s Favor: `{level}`',
            'REPUTATION_LEVEL_TEXT': '\nReputation level: `{level}`',
            'ANEMOCULUS': 'Anemoculus',
            'GEOCULUS': 'Geoculus',
            'ELECTROCULUS': 'Electroculus',
            'COLLECTED_OCULUS_TEXT': 'Collected oculus',
            'COMMON_CHEST': 'Common:',
            'EXQUISITE_CHEST': 'Exquisite',
            'PRECIOUS_CHEST': 'Precious',
            'LUXURIOUS_CHEST': 'Luxurious',
            'CHESTS_OPENED': 'Chest\'s opened',
            'UNLOCKED_TELEPORTS': 'Unlocked waypoints teleports',
            'UNLOCKED_DOMAINS': 'Unlocked domains',
            'MISC_INFO': 'Misc'
        },
        'GENSHIN_CHARACTERS_LIST_COMMAND': {
            'EMBED_GENSHIN_CHARACTERS_LIST_TITLE': 'Genshin Impact. Characters',
            'CHARACTER_LEVEL': 'Level',
            'CHARACTER_CONSTELLATION': 'Constellation',
            'CHARACTER_VISION': 'Vision',
            'CHARACTER_WEAPON': 'Weapon',
        },
        'GENSHIN_CHARACTERS_COMMAND': {
            'INFORMATION_TEXT': '**Information**',
            'CHARACTER_LEVEL': 'Level',
            'CHARACTER_CONSTELLATION': 'Constellation',
            'CHARACTER_VISION': 'Vision',
            'CHARACTER_FRIENDSHIP': 'Friendship level',
            'WEAPON_TEXT': '**Weapon**',
            'WEAPON_NAME': 'Name',
            'WEAPON_RARITY': 'Rarity',
            'WEAPON_TYPE': 'Type',
            'WEAPON_LEVEL': 'Level',
            'WEAPON_ASCENSION_LEVEL': 'Level of ascension',
            'WEAPON_REFINEMENT_LEVEL': 'Level of refinement',
            'ARTIFACTS_TEXT': '**Artifacts**',
            'ARTIFACT_NAME': 'Name',
            'ARTIFACT_RARITY': 'Rarity',
            'ARTIFACT_LEVEL': 'Level',
            'GENSHIN_CHARACTER_VISION': {
                'Anemo': '<:Element_Anemo:870989749534486538> `Anemo`',
                'Pyro': '<:Element_Pyro:870989754454396998> `Pyro`',
                'Hydro': '<:Element_Hydro:870989753649102909> `Hydro`',
                'Electro': '<:Element_Electro:870989752801837056> `Electro`',
                'Geo': '<:Element_Geo:870989753271603230> `Geo`',
                'Dendro': '<:Element_Dendro:870989751908446250> `Dendro`',
                'Cryo': '<:Element_Cryo:870989751312846868> `Cryo`',
            },
            'GENSHIN_ARTIFACT_TYPE': {
                'flower': '<:Icon_Flower_of_Life:871372154179059742> Flower',
                'feather': '<:Icon_Plume_of_Death:871372154510397470> Feather',
                'hourglass': '<:Icon_Sands_of_Eon:871372154845933568> Hourglass',
                'goblet': '<:Icon_Goblet_of_Eonothem:871372154346827776> Goblet',
                'crown': '<:Icon_Circlet_of_Logos:871372154212605962> Crown',
            }
        },
        'GENSHIN_INFO_COMMAND': {
            'NICKNAME_TEXT': 'Nickname',
            'ADVENTURE_RANK_TEXT': 'Rank of Adventure',
            'ACHIEVEMENTS_TEXT': 'Achievements',
            'CHARACTERS_TEXT': 'Characters',
            'SPIRAL_ABYSS_TEXT': 'Spiral Abyss',
            'PLAYER_INFO_TEXT': 'Information about player',
        },
        'SET_EMBED_COLOR_COMMAND': {
            'WRONG_COLOR': 'Wrong color format',
            'SUCCESSFULLY_CHANGED': 'Embed color was changed!'
        },
        'LEVELS': {
            'FUNC_UPDATE_MEMBER': {
                'NOTIFY_GUILD_CHANNEL': '{member} reached level `{level}` and got role {role}',
                'NOTIFY_DM': 'You reached level `{level}` and got role {role}'
            },
            'FUNC_TOP_MEMBERS': {
                'TITLES': '**ID | Member | Current Level**\n',
                'TOP_MEMBERS_TEXT': 'Top members by level',
                'REQUESTED_BY_TEXT': 'Requested by'
            }
        },
        'HELP_COMMAND': {
            'INFORMATION_TEXT': 'Information',
            'INFORMATION_CONTENT_TEXT': '```Hint: [required argument] (optional argument)```',
            'REQUIRED_BY_TEXT': 'Required by {user}',
            'PLUGINS_TEXT': 'Plugins',
            'SELECT_MODULE_TEXT': 'Select Module'
        },
        'STARBOARD_FUNCTIONS': {
            'CHANNEL_WAS_SETUP_TEXT': 'Channel was set up!',
            'LIMIT_WAS_SETUP_TEXT': 'Stars limit was set up to `{limit}`!',
            'STARBOARD_NOT_SETUP': 'Channel or stars limit doesn\'t set up!',
            'STARBOARD_ENABLED': 'Starboard was `enabled`!',
            'STARBOARD_DISABLED': 'Starboard was `disabled`!',
            'JUMP_TO_ORIGINAL_MESSAGE_TEXT': 'Jump to original message!',
            'BLACKLIST_NO_OPTIONS_TEXT': 'Should be one of `member`, `role`, `channel`',
            'EMPTY_BLACKLIST_TEXT': 'Blacklist is empty!',
            'BLACKLIST_ADDED_TEXT': 'Added!',
            'BLACKLIST_REMOVED_TEXT': 'Removed!',
            'BLACKLIST_TEXT': '⭐Starboard. Blacklist',
            'MEMBERS': 'Members',
            'CHANNELS': 'Channels',
            'ROLES': 'Roles'
        },
        'AUTOROLE_DROPDOWN': {
            'ADDED_ROLES_TEXT': 'Added Roles: ',
            'REMOVED_ROLES_TEXT': '\nRemoved Roles: ',
            'NO_OPTIONS_TEXT': 'No options',
            'CREATED_DROPDOWN_TEXT': 'Dropdown created!',
            'MESSAGE_WITHOUT_DROPDOWN_TEXT': 'Message without dropdown!',
            'OPTIONS_OVERKILL_TEXT': 'You can\'t add more than 25 options in dropdown!',
            'SELECT_ROLE_TEXT': 'Select role',
            'ROLE_ADDED_TEXT': 'Role added!',
            'OPTION_NOT_FOUND_TEXT': 'Could not find an option with this name',
            'OPTIONS_LESS_THAN_1_TEXT': 'Options in dropdown can\'t be less than 1',
            'ROLE_REMOVED_TEXT': 'Role removed!',
            'DROPDOWN_ENABLED_TEXT': 'Dropdown enabled!',
            'DROPDOWN_DISABLED_TEXT': 'Dropdown disabled!',
            'DROPDOWN_SAVED_TEXT': 'Dropdown saved!',
            'NOT_SAVED_DROPDOWNS': 'No dropdowns saved!',
            'DROPDOWN_NOT_FOUND': 'Could not find Dropdown with this name',
            'DROPDOWN_LOADED_TEXT': 'Dropdown loaded!',
            'DROPDOWN_LIST': 'Dropdowns list'
        },
        'AUTOROLE_ON_JOIN': {
            'ROLE_ADDED_TEXT': 'Role {role} Added!',
            'ROLE_REMOVED_TEXT': 'Role {role} Removed!'
        },
        'TIME_FORMATS': {
            'с': 'seconds',
            'м': 'minutes',
            'ч': 'hours',
            'д': 'days',
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
        },
        'COMMAND_CONTROL': {
            'COMMAND_DISABLED': 'Command `{}` was disabled!',
            'COMMAND_ENABLED': 'Command `{}` was enabled!'
        }
    }
}
