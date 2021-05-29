from threading import Thread
import os

def run():
  os.system('java -jar Lavalink.jar')

def start_lavalink():
  thread = Thread(target=run)
  thread.start()