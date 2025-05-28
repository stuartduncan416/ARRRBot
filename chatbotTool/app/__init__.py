from flask import Flask
from config import Config
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
from flask_session import Session
import os

app = Flask(__name__)
app.debug = True
app.permanent_session_lifetime = timedelta(hours=1)  # Set the session lifetime to 1 hour
app.config.from_object(Config)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
Session(app)

# Set up a file handler for logging
file_handler = RotatingFileHandler('flask.log', maxBytes=10240, backupCount=10)
file_handler.setLevel(logging.DEBUG)
# Define the format for logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# Add the file handler to the app's logger
app.logger.addHandler(file_handler)

from app import routes

