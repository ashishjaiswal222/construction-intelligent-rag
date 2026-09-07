from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging

logger = logging.getLogger(__name__)

class LanguageDetector:
    def detect(self, text: str) -> str:
        """
        Uses langdetect library to detect language.
        Returns 'en', 'hi', 'mixed', or 'unknown'.
        """
        if not text or len(text.strip()) < 10:
            return "unknown"
            
        try:
            langs = detect_langs(text)
            detected_codes = [l.lang for l in langs]
            
            if 'hi' in detected_codes and 'en' in detected_codes:
                return 'mixed'
            elif 'hi' in detected_codes:
                return 'hi'
            elif 'en' in detected_codes:
                return 'en'
            else:
                return 'unknown'
        except LangDetectException as e:
            logger.error(f"Error detecting language: {str(e)}")
            return "unknown"
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {str(e)}")
            return "unknown"
