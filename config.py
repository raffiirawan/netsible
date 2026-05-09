import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'netsible-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANSIBLE_PLAYBOOKS_DIR = os.path.join(basedir, 'ansible', 'playbooks')
    ANSIBLE_INVENTORY_DIR = os.path.join(basedir, 'ansible', 'inventory')


class DevelopmentConfig(Config):
    """Development configuration — SQLite."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'netsible.db')


class ProductionConfig(Config):
    """Production configuration — PostgreSQL / MySQL."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'netsible.db')
    )


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
