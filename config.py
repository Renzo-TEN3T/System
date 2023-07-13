class Config:
    SECRET_KEY = 'mysecretkey'

class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'abcd1234'
    MYSQL_DB = 'process'


config = {
    'development':DevelopmentConfig
}