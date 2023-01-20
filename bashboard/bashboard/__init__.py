from flask import Flask
from flask_socketio import SocketIO
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config.from_object(Config)
sio = SocketIO(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from bashboard import routes, models

if __name__ == '__main__':
    sio.run(app)
