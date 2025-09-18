"""
Configuration module for RoadBox
Centralized configuration management
"""

import os


class Config:
    """Base configuration class"""

    # Pathfinding settings
    PATHFINDING_TOLERANCE = float(os.environ.get('PATHFINDING_TOLERANCE', 0.5))

    # Server settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    THREADED = True
    USE_RELOADER = DEBUG

    # Data settings
    MAX_FEATURES = int(os.environ.get('MAX_FEATURES', 10000))
    CACHE_DATASETS = True

    # Network settings
    NETWORK_TOLERANCE = float(os.environ.get('NETWORK_TOLERANCE', 0.002))  # ~200m


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    USE_RELOADER = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    USE_RELOADER = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])