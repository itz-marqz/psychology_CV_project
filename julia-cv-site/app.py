from pathlib import Path
import os

from flask import Flask, abort, send_from_directory

SITE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(SITE_DIR, "index.html")


@app.get("/<path:filename>")
def site_file(filename: str):
    target = (SITE_DIR / filename).resolve()
    if not target.is_relative_to(SITE_DIR):
        abort(404)
    return send_from_directory(SITE_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
