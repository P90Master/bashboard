import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'giuq984gfh8fhi4gt8yt82h2eihjdhf94yt8960-221wopaslc'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        "postgresql://postgres:88880000@127.0.0.1:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
