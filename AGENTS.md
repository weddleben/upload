# AGENTS.md

## Project
Simple Flask file hosting site with drag-and-drop upload UI.

## Stack
Python, Flask 3.1.3, Jinja2 templates, vanilla JS/CSS

## Run the App
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
flask run --debug

## Architecture
- Entry: `application.py` → `app/__init__.py` creates the Flask app
- Routes: `app/upload/views.py` (upload endpoints), `app/misc/views.py` (error handlers)
- Templates: `app/templates/` (Jinja2)
- Static: `app/static/` (CSS/JS)

## API
- GET / - home page (upload UI)
- PUT /upload/newfile - upload file (currently stub)

## Notes
- No tests, linting, or CI configured
- `strict_slashes = False` on url_map
- `venv/` and `__pycache__/` are gitignored
- Do not commit anything or push to remote without confirming with the user first
