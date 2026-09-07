# Phase 2: Services and Engines

The core intelligence of Phase 2 lives within the Services layer. This layer manages how images are manipulated, how routing decisions are made, and how data is requested from external AI models.

---

## 1. Image Preprocessing Service

Before any OCR engine touches an image, it passes through `ImagePreprocessor`. Construction documents are notoriously difficult to read (faded blueprints, coffee stains, low DPI scans).
- **Upscaling**: If an image is smaller than 1200x1600, it is upscaled using `Image.Resampling.LANCZOS` while maintaining the exact aspect ratio.
- **Grayscale**: Converted to 'L' mode to drop unnecessary color channels that confuse OCR models.
- **Contrast**: A 1.5x contrast multiplier is applied to make faded text "pop" against the background.

Additionally, a `StampDetector` uses headless OpenCV (`cv2`) and Otsu thresholding to find circular or rectangular engineering stamps based on contour aspect ratios.

---

## 2. The OCR Router (`ocr_router.py`)

A hardcoded, strict decision tree that balances cost, speed, and accuracy:
1. **Digital Text Layer**: If PyMuPDF extracts text, and our heuristics (character count, alpha ratio) score it > 0.85, we skip AI entirely. (Fastest, Cheapest).
2. **Handwriting / Drawings**: If the page contains handwriting or complex architectural drawings, it routes directly to `GEMINI_VISION`.
3. **Tables**: If it's a Bill of Quantities (BOQ) with tables, it routes to `GEMINI_VISION`.
4. **Standard Text**: Defaults to `PADDLE_OCR` (Local, Free).

---

## 3. The Extraction Engines

### PaddleService
Runs locally using the `paddleocr` python wrapper. Configured with `use_angle_cls=True` to automatically fix upside-down or rotated scans. Extremely fast for standard alphanumeric text.

### GeminiVisionService
The heavy lifter. Connects to `gemini-2.0-flash`. 
- Used for complex spatial understanding (tables, diagrams).
- Prompts are injected from `prompts/handwriting_prompt.py`. The LLM is strictly instructed to return *only* JSON arrays, stripping out conversational filler or markdown code fences.

### EnsembleService
The safety net. When a page routes to `PaddleService`, the Ensemble monitors the confidence score. If PaddleOCR reports a confidence below `0.78`, the Ensemble intercepts the return, drops the Paddle result, and automatically escalates the image to `GeminiVisionService` to try again.

---

## 4. OCR Quality Assessment (`ocr_quality_service.py`)

Every extracted text block is audited before saving. The quality score isn't just trusting the OCR engine's self-reported confidence. We calculate:
- **Alpha Ratio**: The percentage of standard alphabetical characters vs total length.
- **Symbol Density**: Checks if the OCR hallucinated blocks of garbage characters (e.g., `!@#$%^&*`).
- **Word Density**: Evaluates whitespace and word formation.

If the final combined heuristic score is `< 0.55`, the service throws an exception, causing the Celery task to retry the page.

---

## 5. Recent Stabilizations & Fixes

During End-to-End testing, several critical bugs were resolved within the Services layer:

1. **Environment Variable Loading**: Discovered that `settings.env()` was causing `AttributeError: 'Settings' object has no attribute 'env'`. Refactored `GeminiVisionService`, `TableExtractor`, and `DrawingUnderstandingService` to strictly use `os.environ.get()` for retrieving API keys.
2. **API Key Priority**: Updated the configuration to check for both `GOOGLE_API_KEY` and `GEMINI_API_KEY`, prioritizing `GOOGLE_API_KEY` to ensure compatibility with the updated `google-generativeai` SDK.
3. **Table Extraction Graceful Degradation**: When Gemini hits a `429 Quota Exceeded` on the Free Tier, the `TableExtractor` now catches the exception rather than crashing the entire worker, allowing the text-layer extraction to successfully save and continue.
