import os
import threading

from discord_bot import bot
from flask_app import run_flask

TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    # Start Flask server in a thread
    threading.Thread(target=run_flask).start()

    # Run your Discord bot
    bot.run(TOKEN)
