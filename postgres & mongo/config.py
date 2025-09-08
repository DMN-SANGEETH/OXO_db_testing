"""Configuration"""
import os
from dotenv import load_dotenv


load_dotenv()


class GeminiConfig:
    """Gemini Configurations"""

    @staticmethod
    def get_gemini_api_key() -> str:
        """Gemini API key"""
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            print("GEMINI_API_KEY not set in environment variables")
        print("key",key)
        return key

class MongoDBConfig:
    """Mongo DB Configurations"""

    @staticmethod
    def get_mongodb_uri() -> str:
        """Mongo DB uri"""
        uri = os.getenv("MONGO_URI")
        if not uri:
            print("MONGO_URI not set in environment variables")
        return uri