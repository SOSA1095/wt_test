import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    WTF_CSRF_ENABLED = False
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = 'postgresql:///t247_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    # os.environ.get("DATABASE_URL")
    # postgres://sbmvjnstodirdq:da2890133f95e99bfcf7cb5a3631e9b164ce2e8cd570e235aa718ba47a83230b@ec2-174-129-32-37.compute-1.amazonaws.com:5432/demqd7v1u6naso
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgres://sbmvjnstodirdq:da2890133f95e99bfcf7cb5a3631e9b164ce2e8cd570e235aa718ba47a83230b@ec2-174-129-32-37.compute-1.amazonaws.com:5432/demqd7v1u6naso"
    DATABASE_URL = "postgres://sbmvjnstodirdq:da2890133f95e99bfcf7cb5a3631e9b164ce2e8cd570e235aa718ba47a83230b@ec2-174-129-32-37.compute-1.amazonaws.com:5432/demqd7v1u6naso"


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
