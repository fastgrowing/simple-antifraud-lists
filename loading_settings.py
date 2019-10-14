from dotenv import load_dotenv
import os

# Loading the local env
def load_variables():
    APP_ROOT = os.path.dirname(__file__)
    env_path = os.path.join(APP_ROOT, '.env')
    load_dotenv(env_path)
    configs = dict()
    configs['SANIC_PORT'] = int(os.getenv('SANIC_PORT'))
    configs['SANIC_DEBUG'] = os.getenv('SANIC_DEBUG')
    configs['REDIS_HOST'] = os.getenv('REDIS_HOST')
    configs['REDIS_PORT'] = int(os.getenv('REDIS_PORT'))
    configs['REDIS_DB'] = int(os.getenv('REDIS_DB'))
    configs['SENTRY_URL'] = str(os.getenv('SENTRY_URL'))
    configs['SANIC_REQUEST_MAX_SIZE'] = int(os.getenv('SANIC_REQUEST_MAX_SIZE'))
    configs['SANIC_KEEP_ALIVE_TIMEOUT'] = int(os.getenv('SANIC_KEEP_ALIVE_TIMEOUT'))
    return configs
