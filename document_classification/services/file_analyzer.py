import os
import hashlib
import magic
import fitz  # PyMuPDF
from ..schemas.classification import FileAnalysisResult

class FileAnalyzerService:
    @staticmethod
    def analyze(file_path: str) -> FileAnalysisResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        mime_type = magic.from_file(file_path, mime=True)
        file_hash = FileAnalyzerService._calculate_hash(file_path)
        
        page_count = None
        preview = ""
        has_images = False

        if mime_type == 'application/pdf':
            preview, page_count, has_images = FileAnalyzerService._analyze_pdf(file_path)
        elif mime_type.startswith('text/'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                preview = f.read(2500)
                page_count = 1

        return FileAnalysisResult(
            mime_type=mime_type,
            file_hash=file_hash,
            file_size=file_size,
            page_count=page_count,
            preview_text=preview,
            has_images=has_images
        )

    @staticmethod
    def _calculate_hash(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def _analyze_pdf(file_path: str) -> tuple[str, int, bool]:
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            text_parts = []
            has_images = False
            
            pages_to_read = list(range(min(3, page_count)))
            if page_count > 3:
                pages_to_read.append(page_count - 1)
                
            for i in pages_to_read:
                page = doc[i]
                text_parts.append(page.get_text()[:800])
                if page.get_images(): 
                    has_images = True
            return '\n'.join(text_parts), page_count, has_images
        except Exception as e:
            return f'Could not extract text: {e}', 0, False
