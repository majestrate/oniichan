from oniichan import db

class DetectedSpam(Exception):
    pass


def get_spam_strings():
    with db.open() as session:
        yield from session.get_spam_strings()

def data_is_spam(data):
    # TODO: implement
    if len(data) > 64:
        return True
    return False

def post_is_spam(data):
    if len(data) > 4096:
        return True

    for spam in get_spam_strings():
        if spam in data:
            return True
    return False

def detect(data, is_post=False):
    """
    detect spam from string
    """
    if is_post:
        if post_is_spam(data):
            raise DetectedSpam()
    elif data_is_spam(data):
        raise DetectedSpam()
