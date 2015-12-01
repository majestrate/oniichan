import os

_root = os.path.abspath(os.getcwd())
board_base_dir = os.path.join(_root, "boards")
media_dir = os.path.join(_root, "media")
template_dirs = [ os.path.join(_root, "oniichan", "templates") ]
enable_tor = True
db_url = 'sqlite:///oniichan.db3'
post_ratelimit = 30

CSRF_ENABLED = True
SECRET_KEY = os.urandom(64)
MAX_CONTENT_LENGTH = 8 * 1024 * 1024
