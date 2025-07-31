#!/usr/bin/env python3
"""
General utility functions and helpers.
"""

import hashlib
import io
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

def create_hash(text: str) -> str:
    """Create MD5 hash of text for comparison purposes.
    
    Args:
        text: Text to hash
        
    Returns:
        MD5 hash string
    """
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate basic word overlap similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if len(words1) == 0 or len(words2) == 0:
        return 0.0
    
    overlap = len(words1.intersection(words2))
    return overlap / max(len(words1), len(words2))

def is_recent_date(date_string: str, days: int = 7) -> bool:
    """Check if a date string represents a recent date.
    
    Args:
        date_string: ISO format date string
        days: Number of days to consider as recent
        
    Returns:
        True if date is within the recent period, False otherwise
    """
    try:
        date_obj = datetime.fromisoformat(date_string)
        cutoff = datetime.now() - timedelta(days=days)
        return date_obj >= cutoff
    except (ValueError, TypeError):
        return False

def format_date_for_display(date_string: str) -> str:
    """Format an ISO date string for display.
    
    Args:
        date_string: ISO format date string
        
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.fromisoformat(date_string)
        return date_obj.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return "Unknown"

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format.
    
    Returns:
        Current timestamp as ISO string
    """
    return datetime.now().isoformat()

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    return ' '.join(text.strip().split())

def export_data_to_csv(data: List[Dict[str, Any]], headers: List[str]) -> Optional[str]:
    """Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        headers: Column headers
        
    Returns:
        CSV string or None if empty data
    """
    if not data:
        return None
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(headers)
    
    # Write data
    for item in data:
        row = [item.get(header.lower().replace(' ', '_'), '') for header in headers]
        writer.writerow(row)
    
    return output.getvalue()

def validate_url(url: str) -> str:
    """Validate and normalize a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

def count_characters(text: str) -> int:
    """Count characters in text.
    
    Args:
        text: Text to count
        
    Returns:
        Character count
    """
    return len(text.strip())

def get_platform_icon(char_count: int) -> str:
    """Get appropriate icon based on character count for different platforms.
    
    Args:
        char_count: Number of characters
        
    Returns:
        Icon string
    """
    if char_count <= 280:
        return "✅"
    elif char_count <= 400:
        return "⚠️"
    else:
        return "❌"

def clear_session_keys(keys: List[str]) -> int:
    """Clear specified keys from Streamlit session state.
    
    Args:
        keys: List of session state keys to clear
        
    Returns:
        Number of keys cleared
    """
    cleared_count = 0
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
            cleared_count += 1
    return cleared_count
