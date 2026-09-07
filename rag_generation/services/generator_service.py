import os
import logging
from rag_generation.prompts.generation_prompt import GENERATION_PROMPT, FALLBACK_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class GeneratorService:
    """
    Calls Groq (or configured model) with the generation prompt, with automatic Gemini fallback.
    """

    MODEL = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
    MAX_TOKENS = 1024
    TEMPERATURE = 0.1

    FAILURE_MESSAGE = (
        "I was unable to generate an answer at this time due to "
        "a technical error. Please try again or contact support."
    )

    def __init__(self, groq_api_key: str):
        from langchain_groq import ChatGroq
        self.model = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
        self.MODEL = self.model
        self.llm = ChatGroq(
            model=self.model,
            api_key=groq_api_key,
            temperature=self.TEMPERATURE,
            max_tokens=self.MAX_TOKENS,
        )

    def _call_gemini_fallback(self, prompt: str) -> str:
        gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if gemini_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            for gemini_model in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                try:
                    gemini_llm = ChatGoogleGenerativeAI(
                        model=gemini_model,
                        google_api_key=gemini_key,
                        temperature=self.TEMPERATURE,
                    )
                    res = gemini_llm.invoke(prompt)
                    return res.content
                except Exception as e:
                    logger.warning(f"Gemini model {gemini_model} fallback failed: {e}")
        return ""

    def generate(
        self,
        user_query: str,
        context_string: str,
        needs_fallback: bool,
    ) -> str:
        """
        Formats GENERATION_PROMPT with query and context.
        Calls Groq, falling back to Gemini if needed. Returns answer string.
        """
        if not context_string:
            return self.FAILURE_MESSAGE

        prompt_template = FALLBACK_GENERATION_PROMPT if needs_fallback else GENERATION_PROMPT
        prompt = prompt_template.format(user_query=user_query, context=context_string)
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.warning(f"Groq generation failed with {self.model}: {e}. Trying Gemini fallback.")
            fallback = self._call_gemini_fallback(prompt)
            if fallback:
                return fallback
            return self.FAILURE_MESSAGE

    def rewrite_query(self, user_query: str, chat_history: list[dict]) -> str:
        if not chat_history:
            return user_query
            
        history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in chat_history])
        prompt = f"""Given the following conversation history and the latest user query, rewrite the query so it is a standalone question that can be understood without the context. If it already makes sense standalone, just return the exact query.
        
History:
{history_str}

Latest Query: {user_query}

Rewritten Query:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.warning(f"Groq query rewrite failed: {e}. Trying Gemini fallback.")
            fallback = self._call_gemini_fallback(prompt)
            if fallback:
                return fallback.strip()
            return user_query

    def classify_intent(self, user_query: str) -> str:
        prompt = f"""Is the following user query conversational (e.g., greetings, stating personal facts, small talk like "hi", "my name is...", "how are you") or a document search (e.g., "what is the penalty", "find the clause", "summarize")?
Reply ONLY with the word "CHAT" or "SEARCH". Do not include any other text.

Query: "{user_query}"
"""
        try:
            res = self.llm.invoke(prompt)
            return "CHAT" if "CHAT" in res.content.upper() else "SEARCH"
        except Exception:
            fallback = self._call_gemini_fallback(prompt)
            if fallback and "CHAT" in fallback.upper():
                return "CHAT"
            return "SEARCH"

    def generate_conversational_response(self, user_query: str, chat_history: list[dict], mem0_context: str) -> str:
        history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in chat_history[-4:]])
        prompt = f"""You are a helpful and polite construction AI assistant. The user is just chatting or stating a fact.
Respond naturally and concisely.

Long-term Memory Context about the User:
{mem0_context}

Recent Chat History:
{history_str}

User: {user_query}
Assistant:"""
        try:
            res = self.llm.invoke(prompt)
            return res.content.strip()
        except Exception:
            fallback = self._call_gemini_fallback(prompt)
            if fallback:
                return fallback.strip()
            return "Hello! How can I help you with your construction documents today?"
