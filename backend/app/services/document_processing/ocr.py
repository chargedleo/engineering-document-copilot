import logging
import os
import shutil
import sys
from typing import Optional, Union
import cv2
import numpy as np
from PIL import Image
import pytesseract

from app.core.config import settings

logger = logging.getLogger("engineering_copilot.ocr")


class TesseractNotFoundError(RuntimeError):
    """Raised when Tesseract OCR executable cannot be found and OCR is requested."""
    pass


def find_tesseract_cmd() -> Optional[str]:
    """
    Discover the Tesseract OCR executable.
    Resolution order:
    1. settings.TESSERACT_CMD (if configured and exists)
    2. PATH environment variable discovery (shutil.which)
    3. Standard Windows installation paths (fallback)
    """
    # 1. Configured path from settings
    if settings.TESSERACT_CMD:
        cmd = str(settings.TESSERACT_CMD).strip().strip('"').strip("'")
        if os.path.isfile(cmd):
            return cmd

    # 2. Discovery on system PATH
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    # 3. Windows standard installation locations
    if sys.platform == "win32":
        candidate_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for candidate in candidate_paths:
            if os.path.isfile(candidate):
                return candidate

    return None


def is_tesseract_available() -> bool:
    """Check whether Tesseract OCR is installed and accessible."""
    return find_tesseract_cmd() is not None


def configure_tesseract() -> str:
    """
    Ensure pytesseract is configured with the discovered executable path.
    Raises TesseractNotFoundError if not located.
    """
    cmd = find_tesseract_cmd()
    if not cmd:
        raise TesseractNotFoundError(
            "Tesseract OCR executable was not found. Please verify Tesseract is installed "
            "and on PATH, or set TESSERACT_CMD in your .env file (e.g. C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
        )
    pytesseract.pytesseract.tesseract_cmd = cmd
    return cmd


def preprocess_image_for_ocr(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
    """
    Apply OpenCV preprocessing to optimize image for OCR extraction on technical documents:
    1. Conversion to single-channel grayscale.
    2. Light Gaussian filtering to suppress scan grain and sensor noise.
    3. Otsu binarization to establish high contrast between text and background.
    """
    if isinstance(image, Image.Image):
        # Convert PIL Image to RGB numpy array
        img_np = np.array(image.convert("RGB"))
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    else:
        img_bgr = image

    # 1. Grayscale
    if len(img_bgr.shape) == 3:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_bgr

    # 2. Denoising: 3x3 Gaussian blur reduces scan artifacts without blurring thin technical lines
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3. Binarization: Otsu's thresholding automatically computes optimal global threshold
    _, binarized = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binarized


def perform_ocr(image: Union[Image.Image, np.ndarray], lang: str = "eng") -> str:
    """
    Execute Tesseract OCR on a page image using OpenCV preprocessing.
    """
    configure_tesseract()
    preprocessed = preprocess_image_for_ocr(image)

    # PSM 1: Automatic page segmentation with OSD (orientation & script detection)
    # or default automatic page segmentation
    custom_config = r"--oem 3 --psm 3"
    raw_text = pytesseract.image_to_string(preprocessed, lang=lang, config=custom_config)

    # Normalize text (clean excessive trailing spaces, keep symbols/punctuations)
    lines = [line.rstrip() for line in raw_text.splitlines()]
    cleaned_text = "\n".join(lines).strip()
    return cleaned_text
