from flask import Flask

app = Flask(__name__)
app.url_map.strict_slashes = False

from app.upload import views
from app.misc import views