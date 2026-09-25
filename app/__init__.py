from flask import Flask

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['MAX_CONTENT_LENGTH'] = 1024 ** 3  # 1GB

from app.upload import views
from app.misc import views