from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()


class Files(db.Model):
    def __init__(self, file_key, orginal_name, internal_name, ftype):
        self.file_key = file_key
        self.orginal_name = orginal_name
        self.internal_name = internal_name
        self.ftype = ftype

    id = db.Column(db.Integer, primary_key=True)
    file_key = db.Column(db.String(), nullable=False, unique=True)
    orginal_name = db.Column(db.String(), nullable=False, unique=False)
    internal_name = db.Column(db.String(), nullable=False, unique=True)
    isdeleted = db.Column(db.Boolean(), nullable=False, unique=False, default=False)
    ftype = db.Column(db.String(), nullable=False, unique=False)
    uploaded_on = db.Column(db.Integer(), nullable=False, default=int(time.time()))
    processed = db.Column(db.Boolean(), nullable=False, default=False)
