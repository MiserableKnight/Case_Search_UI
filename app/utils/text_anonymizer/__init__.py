from .anonymizer import (
    TextAnonymizer,
    anonymize_text,
    add_sensitive_words,
    add_patterns,
    get_sensitive_words,
    get_patterns
)

__all__ = [
    'TextAnonymizer',
    'anonymize_text',
    'add_sensitive_words',
    'add_patterns',
    'get_sensitive_words',
    'get_patterns'
] 