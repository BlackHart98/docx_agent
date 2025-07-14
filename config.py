import redis.asyncio as aioredis

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


broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL 
