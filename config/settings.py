#!/usr/bin/env python3
"""
Application settings and configuration management.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CaptionSettings:
    """Configuration for caption generation."""
    style: str = "Professional"
    length: str = "Medium (4-6 sentences)"
    use_premium_model: bool = False
    include_cta: bool = True
    focus_keywords: str = ""
    avoid_words: str = ""
    target_audience: str = "General"
    character_limit_preference: str = "No limit"

@dataclass
class CompanyProfile:
    """Company profile data structure."""
    business_input: str = ""
    website_url: str = ""
    caption_style: str = "Professional"
    caption_length: str = "Medium (4-6 sentences)"
    use_premium_model: bool = False
    include_cta: bool = True
    focus_keywords: str = ""
    avoid_words: str = ""
    target_audience: str = "General"
    text_only_mode: bool = False
    character_limit_preference: str = "No limit"
    saved_date: Optional[str] = None
    last_used: Optional[str] = None
    captions_generated_count: int = 1
    website_analysis: Optional[Dict] = None

# === Session State Keys ===
SESSION_KEYS = {
    # Image related
    "IMAGE_KEYS": [
        'current_image', 'original_image', 'batch_images', 'batch_captions',
        'selected_web_image', 'clipboard_image', 'uploaded_image'
    ],
    
    # Caption and generation related
    "CAPTION_KEYS": [
        'generated_captions', 'is_batch_result'
    ],
    
    # Website and business related
    "BUSINESS_KEYS": [
        'website_analysis', 'auto_business', 'auto_filled_business_name',
        'previous_website_url', 'previous_auto_fill'
    ],
    
    # Company profiles and settings
    "PROFILE_KEYS": [
        'selected_company_profile', 'selected_company_name', 
        'editing_company', 'editing_profile'
    ],
    
    # Temporary form inputs
    "TEMP_KEYS": [
        'temp_business_input', 'temp_website_url', 'temp_text_only_mode',
        'temp_caption_style', 'temp_caption_length', 'temp_use_premium_model',
        'temp_include_cta', 'temp_focus_keywords', 'temp_avoid_words',
        'temp_target_audience', 'temp_character_limit_preference'
    ],
    
    # UI state
    "UI_KEYS": [
        'show_save_options', 'show_documentation', 'show_feedback',
        'image_selection_mode', 'company_selector', 'management_mode',
        'delete_selector', 'edit_selector', 'website_url_field'
    ],
    
    # Form field keys that need explicit clearing
    "FORM_KEYS": [
        'business_input_field', 'website_url_input'
    ],
    
    # Authentication related
    "AUTH_KEYS": [
        'password_correct', 'password', 'current_image', 'generated_captions', 
        'website_analysis', 'selected_web_image', 'auto_business', 
        'selected_company_profile', 'selected_company_name', 'editing_company', 
        'editing_profile', 'show_save_options', 'show_documentation', 
        'show_feedback', 'image_selection_mode', 'clipboard_image', 'uploaded_image'
    ]
}

# === Caption Styles ===
CAPTION_STYLES = {
    "Professional": "maintaining a professional, trustworthy tone",
    "Casual & Friendly": "using a warm, conversational, and approachable tone",
    "Inspirational": "focusing on motivation, dreams, and positive transformation",
    "Educational": "providing valuable insights and information",
    "Promotional": "highlighting benefits and encouraging action"
}

# === Caption Lengths ===
CAPTION_LENGTHS = {
    "Short (3-4 sentences)": "3-4 sentences",
    "Medium (4-6 sentences)": "4-6 sentences", 
    "Long (6+ sentences)": "6 or more sentences"
}

# === Character Limits ===
CHARACTER_LIMITS = {
    "Facebook (≤500 chars)": "- IMPORTANT: Each caption must be 500 characters or less for Facebook optimization",
    "Instagram (≤400 chars)": "- IMPORTANT: Each caption must be 400 characters or less for Instagram optimization", 
    "LinkedIn (≤700 chars)": "- IMPORTANT: Each caption must be 700 characters or less for LinkedIn optimization",
    "Twitter/X (≤280 chars)": "- IMPORTANT: Each caption must be 280 characters or less for Twitter/X compatibility",
    "All platforms (≤280 chars)": "- IMPORTANT: Each caption must be 280 characters or less for universal platform compatibility"
}
