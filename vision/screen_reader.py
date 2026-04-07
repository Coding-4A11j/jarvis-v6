"""
Jarvis v6 - Screen Reader
===========================
Captures the screen, extracts text via OCR, and detects error messages.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("jarvis.vision")


@dataclass
class ScreenAnalysis:
    """Result of a screen analysis."""

    text: str = ""
    errors: List[str] = field(default_factory=list)
    has_errors: bool = False
    screenshot_path: Optional[str] = None


class ScreenReader:
    """Capture screen, extract text with OCR, detect error patterns.

    Dependencies:
        - pyautogui   (screenshots)
        - pytesseract  (OCR)
        - opencv-python (image processing)
        - Pillow       (image handling)

    External:
        - Tesseract OCR binary must be installed separately.
          Windows: winget install UB-Mannheim.TesseractOCR
    """

    # Common error patterns to look for in screen text
    ERROR_PATTERNS = [
        r"Traceback \(most recent call last\)",
        r"Error:",
        r"error:",
        r"ERROR",
        r"Exception:",
        r"FAILED",
        r"failed",
        r"SyntaxError",
        r"TypeError",
        r"ImportError",
        r"ModuleNotFoundError",
        r"IndentationError",
        r"NameError",
        r"ValueError",
        r"AttributeError",
        r"FileNotFoundError",
        r"KeyError",
        r"RuntimeError",
        r"ConnectionError",
        r"OSError",
        r"HTTP\s*[45]\d\d",
        r"status\s*code\s*[45]\d\d",
        r"npm ERR!",
        r"ENOENT",
        r"EACCES",
        r"compilation\s+error",
        r"build\s+failed",
    ]

    def __init__(self, screenshot_dir: Optional[Path] = None) -> None:
        self.screenshot_dir = screenshot_dir or Path("screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._tesseract_available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_screen(self) -> ScreenAnalysis:
        """Full pipeline: capture screenshot → OCR → detect errors."""
        result = ScreenAnalysis()

        # Step 1: Capture
        image, path = self.capture_screenshot()
        if image is None:
            result.errors.append("Screenshot capture failed")
            result.has_errors = True
            return result
        result.screenshot_path = str(path)

        # Step 2: Extract text
        text = self.extract_text(image)
        result.text = text

        # Step 3: Detect errors
        errors = self.detect_errors(text)
        result.errors = errors
        result.has_errors = len(errors) > 0

        return result

    def capture_screenshot(self):
        """Take a screenshot and return (PIL.Image, saved_path)."""
        try:
            import pyautogui
        except ImportError:
            logger.error("pyautogui not installed – cannot capture screen")
            return None, None

        try:
            screenshot = pyautogui.screenshot()
            path = self.screenshot_dir / "latest.png"
            screenshot.save(str(path))
            logger.info("Screenshot saved to %s", path)
            return screenshot, path
        except Exception as exc:
            logger.error("Screenshot capture failed: %s", exc)
            return None, None

    def extract_text(self, image) -> str:
        """Extract text from an image using Tesseract OCR.

        Args:
            image: A PIL.Image or a path to an image file.
        """
        if not self._check_tesseract():
            return ""

        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.error("pytesseract or Pillow not installed")
            return ""

        try:
            # If image is a path, open it
            if isinstance(image, (str, Path)):
                image = Image.open(str(image))

            # Pre-process: convert to grayscale for better OCR
            image = self._preprocess(image)

            text = pytesseract.image_to_string(image)
            logger.info("Extracted %d characters from screenshot", len(text))
            return text

        except Exception as exc:
            logger.error("OCR extraction failed: %s", exc)
            return ""

    def detect_errors(self, text: str) -> List[str]:
        """Scan text for known error patterns.

        Returns:
            List of matched error strings (with surrounding context).
        """
        if not text:
            return []

        found: List[str] = []
        lines = text.splitlines()

        for line in lines:
            for pattern in self.ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    cleaned = line.strip()[:200]
                    if cleaned and cleaned not in found:
                        found.append(cleaned)
                    break  # One match per line is enough

        if found:
            logger.info("Detected %d error(s) on screen", len(found))

        return found

    # ------------------------------------------------------------------
    # Image pre-processing
    # ------------------------------------------------------------------

    @staticmethod
    def _preprocess(image):
        """Convert image to grayscale and threshold for better OCR."""
        try:
            import cv2
            import numpy as np
            from PIL import Image

            # PIL → numpy
            img_array = np.array(image)

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Apply adaptive threshold
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2,
            )

            # numpy → PIL
            return Image.fromarray(processed)

        except ImportError:
            logger.warning("opencv-python not available, skipping preprocessing")
            return image
        except Exception as exc:
            logger.warning("Image preprocessing failed: %s", exc)
            return image

    # ------------------------------------------------------------------
    # Tesseract availability check
    # ------------------------------------------------------------------

    def _check_tesseract(self) -> bool:
        """Check whether Tesseract OCR binary is installed."""
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            logger.warning(
                "Tesseract OCR is not installed. Screen analysis will be limited. "
                "Install it: winget install UB-Mannheim.TesseractOCR"
            )
            self._tesseract_available = False

        return self._tesseract_available
