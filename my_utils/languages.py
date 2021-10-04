def get_content(content_type: str, lang: str):
    return LANGUAGES[lang][content_type]

LANGUAGES_LIST = ['ru', 'en']

LANGUAGES = {
    'ru': {
        'ERRORS_DESCRIPTIONS': {
            'TAG_NOT_FOUND': 'Тег не найден!',
            'FORBIDDEN_TAG': 'Этот тег нельзя использовать!',
            'NOT_TAG_OWNER': 'Вы не владелец тега!',
            'UID_NOT_BINDED': 'У вас не привязан UID!',
            'GI_ACCOUNT_NOT_FOUND': 'Аккаунт с таким UID не найден!',
            'GI_DATA_NOT_PUBLIC': 'Профиль закрыт! Откройте профиль на [сайте](https://www.hoyolab.com/genshin/accountCenter/gameRecord)',
            'NOT_CONNECTED_TO_VOICE': 'You not connected to voice channel!',
            'NOT_BOT_OWNER': 'Это команда доступна только владельцу бота!',
            'BOT_MISS_PERMS': '**У бота недостаточно прав!**\nНеобходимые права: ',
            'MISS_PERMS': '**У вас недостаточно прав!**\nНеобходимые права:',
            'CHECK_FAILURE': 'Вы не можете использовать эту команду!'
        },
        'FUNC_RANDOM_NUMBER_OUT_CONTENT': 'Рандомное число: `{}`',
        'FUNC_MEMBER_INFO': {
            'MEMBER_STATUS': {
                'online':'<:s_online:850792217031082051> В сети',
                'dnd':'<:dnd:850792216943525936> Не беспокоить',
                'idle':'<:s_afk:850792216732368937> Отошёл',
                'offline':'<:s_offline:850792217262030969> Не в сети'
            },
            'ABOUT_TITLE': 'Информация о {}',
            'GENERAL_INFO_TITLE': 'Общая информация:',
            'DISCORD_REGISTRATION_TEXT': '**Дата регистрации в Discord:**',
            'JOINED_ON_SERVER_TEXT': '**Дата присоединения на сервер:**',
            'CURRENT_STATUS_TEXT':'**Текущий статус:**',
            'ROLES':'**Роли:**'
        },
        'FUNC_PING': 'Задержка бота `{}` мс',
        'FUNC_ACTIVITIES': {
            'NOT_CONNECTED_TO_CHANNEL_TEXT': 'Вы не подключены к голосовому каналу!',
            'CHOOSE_ACTIVITY_TEXT':'Выберите категорию'
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
        'FUNC_MODERATION_CHANGE_NICK_TEXT': 'Был изменён ник `{}` на `{}`',
        'FUNC_MODERATION_MUTE_MEMBER': {
            'CANNOT_MUTE_BOT_TEXT': 'Вы не можете замутить бота!',
            'WAS_MUTED_TEXT': '{} был отправлен в мут!',
            'TIME_TEXT': '**Время**: {amount} {time_format}\n',
            'REASON_TEXT': '**Причина**: {reason}'
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
        'FUNC_TAGS_BTAG': {
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
            'SAVED_TAG_TEXT': '**Сохранено!**'
        },
        'PLAY_MUSIC_COMMAND': {
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
        }
    },

    'en': {
        'ERRORS_DESCRIPTIONS': {
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
        },
        'FUNC_RANDOM_NUMBER_OUT_CONTENT': 'Random number is `{}`',
        'FUNC_MEMBER_INFO': {
            'MEMBER_STATUS': {
                'online':'<:s_online:850792217031082051> Online',
                'dnd':'<:dnd:850792216943525936> Do not disturb',
                'idle':'<:s_afk:850792216732368937> Idle',
                'offline':'<:s_offline:850792217262030969> Offline'
            },
            'ABOUT_TITLE': 'Information about {}',
            'GENERAL_INFO_TITLE': 'General information:',
            'DISCORD_REGISTRATION_TEXT': '**Date of registration in Discord:**',
            'JOINED_ON_SERVER_TEXT': '**Date of joined in server:**',
            'CURRENT_STATUS_TEXT':'**Current status:**',
            'ROLES':'**Roles:**'
        },
        'FUNC_PING': 'Bot latency is `{}` ms',
        'FUNC_ACTIVITIES': {
            'NOT_CONNECTED_TO_CHANNEL_TEXT': 'You not connected to voice channel!',
            'CHOOSE_ACTIVITY_TEXT':'Choose activity'
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
                '**Players:** {} и {} \n' \
                '**Rounds played:** {} \n' \
                '**Score:** {}:{} \n' \
                '**Winner:** {}',
            'RESULTS_GAME_NAME': '**Game name: Rock Paper Scissors**',
            'RESULTS_TIE': 'Draw',
            'MADE_MOVE_TEXT': 'You made move',
            'PLAYERS_TEXT': '**{}** VS **{}**',
            'CURRENT_SCORE_TEXT': '**Score:** {}:{}\n' \
                '**Match:** {}/{}',
        },
        'FUNC_MODERATION_CHANGE_NICK_TEXT': 'Nick of `{}` was changed to `{}`',
        'FUNC_MODERATION_MUTE_MEMBER': {
            'CANNOT_MUTE_BOT_TEXT': 'You can\'t mute bot!',
            'WAS_MUTED_TEXT': '{} was muted!',
            'TIME_TEXT': '**Timeout**: {amount} {time_format}\n',
            'REASON_TEXT': '**Reason**: {reason}'
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
        'FUNC_TAGS_BTAG': {
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
            'SAVED_TAG_TEXT': '**Saved!**'
        },
        'MUSIC_PLAY_COMMAND': {
            'ADDED_IN_QUEUE_TEXT': '`{}` was added in queue',
            'NOT_CONNECTED_TO_VOICE': 'Connect to voice channel with a bot',
            'PAUSE_BUTTON':'Stop',
            'RESUME_BUTTON':'Resume',
            'STOP_BUTTON':'Stop',
            'SKIP_BUTTON':'Skip',
            'TOGGLE_OFF_BUTTON':'Disable repeat',
            'TOGGLE_ON_BUTTON':'Enable repeat',
            'PLAYING_TEXT':'Now playing',
            'NAME_TEXT':'Name:',
            'DURATION_TEXT':'Duration:',
            'LIVE_TEXT': 'Live',
            'WHO_ADDED_TEXT':'Added {}',
            'SUCCESSFULLY':'Successfully!'
        }
    }
}