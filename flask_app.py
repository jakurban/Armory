import os

from flask import Flask

app = Flask(__name__)


# Simple route for health check
@app.route('/')
def home():
    return "Bot is running!"


# Run Flask app in a separate thread
def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
