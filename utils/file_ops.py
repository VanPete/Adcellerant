#!/usr/bin/env python3
"""
File operations utilities for JSON data management.
"""

import json
import os
from typing import Dict, List, Any, Optional
import streamlit as st

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load data from a JSON file with error handling.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dict containing the loaded data, empty dict if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    except (PermissionError, OSError) as e:
        st.error(f"File access error loading {filepath}: {str(e)}")
        return {}

def save_json_file(filepath: str, data: Any) -> bool:
    """Save data to a JSON file with error handling.
    
    Args:
        filepath: Path to the JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (PermissionError, OSError) as e:
        st.error(f"File access error saving {filepath}: {str(e)}")
        return False
    except (TypeError, ValueError) as e:
        st.error(f"Data serialization error: {str(e)}")
        return False

def load_list_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load a list from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List containing the loaded data, empty list if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    except Exception as e:
        st.error(f"Error loading {filepath}: {str(e)}")
        return []

def append_to_json_list(filepath: str, new_item: Dict[str, Any]) -> bool:
    """Append an item to a JSON list file.
    
    Args:
        filepath: Path to the JSON file
        new_item: Item to append
        
    Returns:
        True if successful, False otherwise
    """
    try:
        data_list = load_list_from_json(filepath)
        data_list.append(new_item)
        return save_json_file(filepath, data_list)
    except Exception as e:
        st.error(f"Error appending to {filepath}: {str(e)}")
        return False

def file_exists(filepath: str) -> bool:
    """Check if a file exists.
    
    Args:
        filepath: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(filepath)

def get_file_size(filepath: str) -> int:
    """Get file size in bytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    except OSError:
        return 0
