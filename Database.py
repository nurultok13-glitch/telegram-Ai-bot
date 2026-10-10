import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class Provider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    CEREBRAS = "cerebras"


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "groq")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.1-70b")
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "100"))
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]
    DB_PATH = os.getenv("DB_PATH", "bot_database.db")

    MODELS = {
        "groq": {
            "llama-3.1-70b": "llama-3.1-70b-versatile",
            "llama-3.1-8b": "llama-3.1-8b-instant",
            "llama-3.2-11b": "llama-3.2-11b-text-preview",
            "llama-3.2-90b": "llama-3.2-90b-vision-preview",
            "mixtral-8x7b": "mixtral-8x7b-32768",
            "gemma2-9b": "gemma2-9b-it",
            "deepseek-r1-distill-70b": "deepseek-r1-distill-llama-70b",
        },
        "gemini": {
            "gemini-1.5-flash": "gemini-1.5-flash",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
            "gemini-1.5-flash-8b": "gemini-1.5-flash-8b",
        },
        "openrouter": {
            "openai/gpt-4o-mini": "openai/gpt-4o-mini",
            "google/gemini-flash-1.5": "google/gemini-flash-1.5",
            "anthropic/claude-3-haiku": "anthropic/claude-3-haiku",
            "mistralai/mistral-7b-instruct": "mistralai/mistral-7b-instruct",
        },
        "cerebras": {
            "llama-3.3-70b": "llama-3.3-70b",
            "llama-3.1-8b": "llama-3.1-8b",
        },
    }

    SYSTEM_PROMPTS = {
        "default": (
            "Anda adalah AI Assistant yang membantu, ramah, dan cerdas. "
            "Anda menjawab dalam bahasa Indonesia secara default, "
            "kecuali pengguna menggunakan bahasa lain. "
            "Jawaban Anda informatif, akurat, dan mudah dipahami. "
            "Gunakan format Markdown untuk jawaban yang panjang."
        ),
        "coder": (
            "Anda adalah expert programmer. Jawab semua pertanyaan teknis "
            "dengan detail. Selalu berikan contoh code yang benar. "
            "Gunakan Markdown code blocks."
        ),
        "creative": (
            "Anda adalah kreatif writer. Buat jawaban yang menarik, "
            "bersemangat, dan penuh imajinasi."
        ),
        "academic": (
            "Anda adalah professor akademik. Jawab secara formal, "
            "detail, dan akademis. Sertakan referensi jika mungkin."
        ),
        "general": "You are a helpful AI assistant. Respond in the user's language.",
    }


config = Config()
