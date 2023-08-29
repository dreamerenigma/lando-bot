# Use flask
from flask import Flask
from threading import Thread

# define flask app
app = Flask('')

# create roiute for home page
@app.route('/')
def main():
    return "server online!"

# Run our flask app in a thread so that the bot and website can run simultaneosly.
def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()
