#!/usr/bin/env python3
"""
Configuration constants for the Social Post Generator application.
"""

import os

# === File Configurations ===
# Data file configurations - These files persist across all users and sessions
COMPANY_DATA_FILE = "company_profiles.json"  # Shared company directory across all users
USED_CAPTIONS_FILE = "used_captions.json" 
FEEDBACK_FILE = "user_feedback.json"
STATS_FILE = "app_statistics.json"

# === Security Configuration ===
APP_PASSWORD = os.getenv("APP_PASSWORD", "adcellerant2025")

# === Feature Flags ===
# Clipboard functionality removed for cleaner UI
CLIPBOARD_FEATURES_ENABLED = False

# === OpenAI Configuration ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Page Configuration ===
PAGE_CONFIG = {
    "page_title": "🚀 Adcellerant Social Caption Generator",
    "page_icon": "📱",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# === Model Configuration ===
OPENAI_MODELS = {
    "premium": "gpt-4o",
    "standard": "gpt-4o-mini"
}

# === Cache Configuration ===
WEBSITE_ANALYSIS_TTL = 300  # 5 minutes
IMAGE_EXTRACTION_TTL = 300  # 5 minutes

# === Request Configuration ===
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# === File Upload Limits ===
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_RESOLUTION = (100, 100)  # Minimum 100x100 pixels
MAX_RESOLUTION = (10000, 10000)  # Maximum 10000x10000 pixels
ALLOWED_FORMATS = ['PNG', 'JPEG', 'JPG', 'WEBP']
