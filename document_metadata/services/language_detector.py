class LanguageDetector:
    """
    Detects language of document text.
    Used to set Document.language field for multilingual filtering.
    Hindi/Urdu annotations on English drawings are common in
    Indian construction — these need multilingual PaddleOCR.
    """

    HINDI_UNICODE_RANGE = range(0x0900, 0x097F)

    def detect(self, text: str) -> str:
        """
        Returns: 'en' | 'hi' | 'mixed' | 'unknown'
        NEVER raises — returns 'unknown' on any failure.
        """
        if not text or len(text) < 50:
            return 'unknown'

        try:
            from langdetect import detect as langdetect_detect
            lang = langdetect_detect(text[:1000])

            if lang in ('hi', 'ur', 'ar'):
                return 'hi'

            if lang == 'en':
                # Check for Hindi characters mixed in
                hindi_chars = sum(
                    1 for c in text
                    if ord(c) in self.HINDI_UNICODE_RANGE
                )
                if hindi_chars > 5:
                    return 'mixed'
                return 'en'

            return 'unknown'

        except Exception:
            return 'unknown'
