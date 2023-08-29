import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

# Inject Flask magic
app = Flask(__name__)

# Load configuration
app.config.from_object('app.config.Config')

# Construct the DB Object (SQLAlchemy interface)
db = SQLAlchemy (app)
Bootstrap(app)
# Enabel migration for our application
Migrate(app, db)

# Import routing to render the pages
from app import views, models
