class EmptyQueue(Exception):
    """Cannot skip because queue is empty"""


class NotConnectedToVoice(Exception):
    """Cannot create the player because bot is not connected to voice"""


class NotPlaying(Exception):
    """Cannot <do something> because nothing is being played"""
