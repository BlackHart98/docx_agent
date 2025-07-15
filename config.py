import os
from dotenv import load_dotenv, find_dotenv

DOT_ENV_PATH = find_dotenv()
load_dotenv(dotenv_path=DOT_ENV_PATH, override=True)

class Config: # I can't think of a better name
    CLAUSE_HASH_PREFIX = "contract_clause"
    DOCX_SCHEMA = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    DEFAULT_RETRY_COUNT = 5
    DEFAULT_DELAY_SECONDS = 2.0
    DEFAULT_LAG_MAX_SECONDS = 0.5 
    TEMPLATE_PATH = "templates/" 
    PROMPT_TEMPLATE_FILE = "prompt_template.txt"
    ROLE_TEMPLATE_FILE = "role_template.txt"
    REDIS_URL = "redis://localhost:6379/0"
    SQL_FILES = "schemas/"
    POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL 

DATABASE_URL = f"postgresql+psycopg2://{Config.POSTGRES_USERNAME}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"