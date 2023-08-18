
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
	
    SECRET_KEY = 'S_U_perS3crEt_KEY#9999'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
