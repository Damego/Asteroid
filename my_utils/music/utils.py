from asyncio import AbstractEventLoop

import aiohttp
import youtube_dl

from .models import Song

options = {
        "format": "bestaudio/best",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0"
}
youtube_dl.utils.bug_reports_message = lambda: ''
ydl = youtube_dl.YoutubeDL(options)


async def youtube_search(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
    index = html.find('watch?v')
    url = ""
    while True:
        char = html[index]
        if char == '"':
            break
        url += char
        index += 1
    url = f"https://www.youtube.com/{url}"
    return url


async def get_video_data(
    url: str,
    search: bool,
    bettersearch: bool,
    loop: AbstractEventLoop
):
    if bettersearch:
        url = await youtube_search(url)
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
    elif search:
        ytdl_options = options.copy()
        ytdl_options['default_search'] = "auto"
        ytdl = youtube_dl.YoutubeDL(ytdl_options)

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        try:
            data = data["entries"][0]
        except Exception:
            return
        del ytdl
    else:
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

    return Song(data)
