import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-12345')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///finance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False