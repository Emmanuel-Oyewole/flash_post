from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Type, Any


def generate_seo_optimized_slug(text: str, max_length: int = 60) -> str:
    """
    Generate an SEO-optimized slug with shorter length and minimal stopwords.
    Recommended for better search engine optimization.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum length (default 60 for SEO)
    
    Returns:
        An SEO-optimized slug string
    """
    return slugify(
        text,
        entities=True,
        decimal=True,
        hexadecimal=True,
        max_length=max_length,
        word_boundary=True,
        separator='-',
        lowercase=True,
        # Minimal stopwords for SEO
        stopwords=['a', 'an', 'and', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with'],
        replacements=[
            ['&', 'and'],
            ['@', 'at'],
            ['%', 'percent'],
            ['+', 'plus'],
            ['=', 'equals'],
        ],
        allow_unicode=False,
    )
