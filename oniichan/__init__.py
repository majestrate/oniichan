from flask import Flask

app = Flask(__name__)
from oniichan import config
from oniichan import views
app.config.from_object('oniichan.config')
