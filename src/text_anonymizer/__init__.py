"""
Text Anonymizer package.
A tool for anonymizing sensitive information in text.
"""

from .anonymizer import (
    anonymize_text,
    add_sensitive_words,
    get_sensitive_words
)

__version__ = "0.1.0"
__all__ = ["anonymize_text", "add_sensitive_words", "get_sensitive_words"] 