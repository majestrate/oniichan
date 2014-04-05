import os

template_paths = ['/var/lib/oniichan/templates/']
board_base_dir = '/srv/www/oniichan/'
media_dir = '/srv/www/oniichan/media/'
enable_tor = True
db_url = 'sqlite:////var/lib/oniichan/oniichan.db3'

CSRF_ENABLED = True
SECRET_KEY = os.urandom(64)
MAX_CONTENT_LENGTH = 8 * 1024 * 1024
