from app import db
from flask_sqlalchemy import SQLAlchemy

class User(db.Model):
    __tablename__ = 'UserTable'

    userID = db.Column(db.String, primary_key=True)
    docName = db.Column(db.String, primary_key=True, nullable=True)
    docID = db.Column(db.String, nullable=True)
