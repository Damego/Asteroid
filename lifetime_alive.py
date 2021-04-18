from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
  return "TEST"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  thread = Thread(target=run)
  thread.start()