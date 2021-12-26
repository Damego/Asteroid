class Song:
    def __init__(self, data: dict, is_looping: bool = False):
        self.source: str = data["url"]
        self.url: str = "https://www.youtube.com/watch?v=" + data["id"]
        self.title: str = data["title"]
        self.name = self.title
        self.description: str = data.get("description")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.views = data["view_count"]
        self.duration = data["duration"]
        self.thumbnail = data["thumbnail"]
        self.channel: str = data["uploader"]
        self.channel_url: str = data["uploader_url"]
        self.is_looping = is_looping
