#!/usr/bin/env python3
"""
Adcellerant Social Caption Generator - Modular Version
Main application entry point.

Author: Adcellerant Team
Version: 3.0 - Modular Architecture
Last Updated: July 2025
"""

# Standard library imports
import os
import sys

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Third-party imports
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Local imports
from config.constants import PAGE_CONFIG, OPENAI_API_KEY
from modules.auth import check_password, show_logout_option, is_authenticated

# === Page Configuration ===
st.set_page_config(**PAGE_CONFIG)

# === Initialize Environment ===
load_dotenv()

@st.cache_resource
def init_openai_client():
    """Initialize OpenAI client with error handling."""
    if not OPENAI_API_KEY:
        st.error("❌ OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        st.stop()
    return OpenAI(api_key=OPENAI_API_KEY)

def main():
    """Main application function."""
    # Check authentication first
    if not check_password():
        return
    
    # Initialize OpenAI client
    client = init_openai_client()
    
    # Show logout option
    show_logout_option()
    
    # Main app content
    st.title("🚀 Adcellerant Social Caption Generator")
    st.markdown("### 📱 AI-Powered Social Media Caption Generator")
    
    # Temporary placeholder content
    st.success("✅ **Modular Architecture Successfully Implemented!**")
    
    st.info("""
    🎯 **Phase 1 Complete**: 
    - ✅ Modular directory structure created
    - ✅ Configuration modules extracted
    - ✅ Authentication module implemented  
    - ✅ Utility functions modularized
    - ✅ Clean imports and dependencies
    """)
    
    st.warning("""
    🚧 **Coming Next in Phase 2**:
    - Extract caption management
    - Extract company profiles
    - Extract website analysis
    - Extract image processing
    - Extract UI components
    - Complete main application logic
    """)
    
    # Show current authentication status
    with st.sidebar:
        st.markdown("### 🔧 Development Info")
        st.markdown(f"**Authenticated:** {'✅ Yes' if is_authenticated() else '❌ No'}")
        st.markdown(f"**OpenAI Client:** {'✅ Ready' if client else '❌ Not Ready'}")
        
        # Show module structure
        with st.expander("📁 Module Structure"):
            st.code("""
            📦 Social Post Generator/
            ├── main.py (new modular entry point)
            ├── social_post_generator.py (original)
            ├── 📁 config/
            │   ├── constants.py
            │   └── settings.py
            ├── 📁 modules/
            │   └── auth.py
            └── 📁 utils/
                ├── file_ops.py
                └── helpers.py
            """)

if __name__ == "__main__":
    main()
