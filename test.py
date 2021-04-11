import json

def get_token(): 
    with open('jsons/config.json', 'r') as f:
        token = json.load(f)

    return token["TOKEN"]

TOKEN = get_token()
print(TOKEN)