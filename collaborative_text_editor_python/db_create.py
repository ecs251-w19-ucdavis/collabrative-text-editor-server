from app import db
from model import *

db.create_all()

db.session.commit()
