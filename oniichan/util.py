
import base64
import datetime
import hashlib
import os
import time

def now():
    return int(time.time())

def recursive_delete(dirname):
    for root, dirs, files in os.walk(dirname):
        for dir in dirs:
            dir = os.path.join(root, dir)
            recursive_delete(dir)
        for file in files:
            file = os.path.join(root, file)
            os.unlink(file)
        os.rmdir(root)

def datetime_now():
    return datetime.datetime.utcnow()

def new_salt():
    return base64.b64encode(os.urandom(32))

def hash_func(data, salt):
    h = hashlib.new('sha512')
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    h.update(data)
    if not isinstance(salt, bytes):
        salt = salt.encode('utf-8')
    h.update(salt)
    return h.hexdigest()

def is_from_i2p(addr):
    return addr is not '127.0.0.1'
