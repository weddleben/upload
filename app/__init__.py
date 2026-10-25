import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

# Load .env from the project root (a real exported environment variable
# always wins over .env). Must run before reading config below.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['MAX_CONTENT_LENGTH'] = 1024 ** 3  # 1GB
app.config['UPLOAD_MASTER_PASSWORD'] = os.environ.get("UPLOAD_MASTER_PASSWORD", "")
upload_directory = Path(os.environ.get("UPLOAD_DIRECTORY") or Path(app.static_folder) / "uploads").expanduser()
if not upload_directory.is_absolute():
    upload_directory = Path(app.root_path).parent / upload_directory
app.config["UPLOAD_DIRECTORY"] = str(upload_directory.resolve())

from app.upload import views
from app.misc import views
from app.auth import views
