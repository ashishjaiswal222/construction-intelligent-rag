import fitz
import os
import uuid
from typing import Tuple, List

def get_page_count(pdf_path: str) -> int:
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except Exception:
        return 0

def extract_page_as_image(pdf_path: str, page_number: int, output_dir: str, dpi: int = 300) -> str:
    """Extracts a single page from a PDF as a high-quality JPEG."""
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"page_{uuid.uuid4().hex[:8]}_{page_number}.jpg")
    
    with fitz.open(pdf_path) as doc:
        # PyMuPDF uses 0-based indexing
        page = doc[page_number - 1]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(out_path, "jpeg")
        
    return out_path
