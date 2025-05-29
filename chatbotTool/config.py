import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # OpenAI settings
    EMBEDDING_MODEL = "text-embedding-3-large"
    COMPLETION_MODEL = "gpt-4o-mini"

    # File paths
    ARTICLES_FILE = "static/articlesSplitTikTok.pkl"
    EMBEDDINGS_FILE = "static/embeddingMerged.pkl"

    # Prompt settings
    MAX_SECTION_LEN = 500
    SEPARATOR = "\n* "
    ENCODING = "gpt2"
    MAX_TOKENS = 2000
    TEMPERATURE = 1

    OPENAI_KEY = os.environ.get('OPENAI_KEY') or ''
    CHAT_PASSWORD = os.environ.get('CHAT_PASSWORD') 