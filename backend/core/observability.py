from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from backend.core.config import settings

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)

def get_langfuse_callback() -> CallbackHandler:
    return CallbackHandler()