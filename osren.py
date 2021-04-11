import os

for file in os.listdir("./"):
    if file.endswith(".mp3"):
        os.rename(file, "song.mp3")