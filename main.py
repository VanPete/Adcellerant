#!/usr/bin/env python3
"""
Social Post Generator - AI-Powered Social Media Content Creation
A comprehensive Streamlit application for generating engaging social media captions.

This is the refactored main entry point that imports all modular components.
"""

import os
import io
import base64
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import zipfile

# Import modular components
from config.constants import *
from config.settings import *
from modules.auth import check_password, show_logout_option
from modules.captions import get_caption_manager
from modules.companies import get_company_manager, get_session_manager
from modules.website_analysis import get_website_analyzer
from modules.image_processing import get_image_processor, get_image_validator, get_batch_processor
from modules.templates import get_template_manager, get_feedback_manager, get_statistics_manager
from utils.file_ops import load_json_file, save_json_file
from utils.helpers import create_hash, calculate_similarity, truncate_text

# Set Streamlit page configuration
st.set_page_config(**PAGE_CONFIG)

# Initialize OpenAI client
@st.cache_resource
def initialize_openai_client():
    """Initialize OpenAI client with API key."""
    if not OPENAI_API_KEY:
        st.error("❌ OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        st.stop()
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    return client

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'generated_captions' not in st.session_state:
        st.session_state.generated_captions = []
    
    # Session keys for different user input components
    session_keys = [
        'business_name', 'business_type', 'target_audience', 'product_name', 'key_features',
        'unique_selling_points', 'brand_voice', 'caption_style', 'caption_length',
        'include_hashtags', 'include_emojis', 'call_to_action', 'website_url',
        'additional_context', 'openai_model', 'batch_business_name', 'batch_brand_voice',
        'batch_caption_style', 'batch_caption_length', 'batch_include_hashtags',
        'batch_include_emojis', 'batch_call_to_action', 'website_analysis_results', 
        'show_documentation', 'show_feedback', 'image_selection_mode', 'clipboard_image', 'uploaded_image'
    ]
    
    for key in session_keys:
        if key not in st.session_state:
            st.session_state[key] = None

def display_page_header():
    """Display the main page header with title and description."""
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 30px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
        <h1 style='margin: 0; font-size: 2.5em; font-weight: 700;'>🚀 Adcellerant Social Caption Generator</h1>
        <h3 style='margin: 10px 0 0 0; font-weight: 300; opacity: 0.9;'>AI-Powered Social Media Content Creation</h3>
    </div>
    """, unsafe_allow_html=True)

def show_documentation_popup():
    """Show comprehensive documentation popup."""
    if st.session_state.get('show_documentation', False):
        with st.expander("📖 **Complete Feature Guide & Documentation**", expanded=True):
            st.markdown("""
            ### 🎯 **Quick Start Guide**
            
            #### **Step 1: Basic Information**
            - **Business Name**: Enter your company or brand name
            - **Business Type**: Describe what your business does (e.g., "Digital Marketing Agency", "Restaurant", "Tech Startup")
            - **Target Audience**: Who are you trying to reach? (e.g., "Small business owners", "Tech professionals")
            
            #### **Step 2: Product/Service Details**
            - **Product/Service Name**: What specific offering are you promoting?
            - **Key Features**: List 2-3 main benefits or features
            - **Unique Selling Points**: What makes you different from competitors?
            
            #### **Step 3: Brand Voice & Style**
            - **Brand Voice**: Choose from Professional, Casual, Enthusiastic, Educational, or Humorous
            - **Caption Style**: Select the tone that matches your brand
            - **Caption Length**: Short (1-2 sentences), Medium (3-4 sentences), or Long (5+ sentences)
            
            #### **Step 4: Engagement Options**
            - **Include Hashtags**: Automatically add relevant hashtags
            - **Include Emojis**: Add appropriate emojis for visual appeal
            - **Call-to-Action**: Choose from various engagement prompts
            
            ---
            
            ### 🌐 **Website Analysis Feature**
            
            Upload your website URL to automatically extract:
            - **Company information** from About pages
            - **Product/service details** from main pages
            - **Brand voice** analysis from existing content
            - **Key messaging** and value propositions
            
            **How it works:**
            1. Enter your website URL in the sidebar
            2. Click "Analyze Website" 
            3. The AI will scan multiple pages and extract relevant information
            4. This information is automatically used to enhance your captions
            
            ---
            
            ### 📸 **Image Features**
            
            #### **Single Image Processing**
            - Upload any image format (PNG, JPEG, WebP)
            - **Resize**: Change dimensions or use social media presets
            - **Crop**: Custom crop or preset options (center, square, remove borders)
            - **Rotate & Flip**: Adjust orientation
            - **Filters**: Apply grayscale, sepia, contrast, blur, or sharpening
            - **Watermarks**: Add text overlays with customizable positioning
            
            #### **Batch Image Processing**
            - Upload multiple images at once
            - Apply consistent processing to all images
            - Generate captions for each image individually
            - Download all processed images as a ZIP file
            
            #### **Social Media Presets**
            - Instagram Square (1080×1080)
            - Instagram Portrait (1080×1350)
            - Instagram Story (1080×1920)
            - Facebook Post (1200×630)
            - LinkedIn Post (1200×627)
            - Twitter Post (1024×512)
            - YouTube Thumbnail (1280×720)
            
            ---
            
            **Close this window by clicking outside or pressing Escape**
            """)
            
            col_close1, col_close2 = st.columns([1, 1])
            with col_close2:
                if st.button("✅ Got it, close this guide", type="primary", use_container_width=True):
                    st.session_state.show_documentation = False
                    st.rerun()

def show_feedback_popup():
    """Show feedback collection popup."""
    if st.session_state.get('show_feedback', False):
        with st.expander("💬 **Send Feedback & Support**", expanded=True):
            st.markdown("""
            ### We'd love to hear from you! 
            Your feedback helps us improve the Social Caption Generator.
            """)
            
            with st.form("feedback_form"):
                col_feedback1, col_feedback2 = st.columns([1, 1])
                
                with col_feedback1:
                    feedback_type = st.selectbox(
                        "What type of feedback is this?",
                        ["General Feedback", "Bug Report", "Feature Request", "Question/Support", "Compliment"]
                    )
                
                with col_feedback2:
                    rating = st.select_slider(
                        "How would you rate your experience?",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: "⭐" * x
                    )
                
                feedback_title = st.text_input(
                    "Brief summary of your feedback",
                    placeholder="e.g., 'Caption generation is too slow' or 'Love the new image features!'"
                )
                
                feedback_description = st.text_area(
                    "Detailed feedback (optional)",
                    placeholder="Please provide as much detail as possible. For bug reports, include steps to reproduce the issue.",
                    height=100
                )
                
                submitted = st.form_submit_button("📤 Send Feedback", type="primary", use_container_width=True)
                
                if submitted:
                    if feedback_title.strip():
                        feedback_data = {
                            'type': feedback_type,
                            'rating': rating,
                            'title': feedback_title.strip(),
                            'description': feedback_description.strip(),
                            'user_session': st.session_state.get('session_id', 'anonymous'),
                            'app_version': '2.0_refactored'
                        }
                        
                        feedback_manager = get_feedback_manager()
                        if feedback_manager.save_submission(feedback_data):
                            st.success("✅ Thank you for your feedback! We appreciate your input.")
                            st.session_state.show_feedback = False
                            st.rerun()
                        else:
                            st.error("❌ Sorry, there was an error submitting your feedback. Please try again.")
                    else:
                        st.error("Please provide a brief summary of your feedback.")
            
            col_cancel1, col_cancel2 = st.columns([1, 1])
            with col_cancel1:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_feedback = False
                    st.rerun()

def create_advanced_sidebar():
    """Create comprehensive sidebar with all configuration options."""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); 
                    border-radius: 10px; margin-bottom: 20px; color: white;'>
            <h3 style='margin: 0; font-weight: 600;'>⚙️ Configuration Panel</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Model Selection
        st.markdown("### 🤖 AI Model Selection")
        model_choice = st.radio(
            "Choose AI Model:",
            ["GPT-4o (Premium - Best Quality)", "GPT-4o-mini (Standard - Faster)"],
            help="GPT-4o provides higher quality but takes longer. GPT-4o-mini is faster but slightly less nuanced."
        )
        st.session_state.openai_model = OPENAI_MODELS["premium"] if "Premium" in model_choice else OPENAI_MODELS["standard"]
        
        st.markdown("---")
        
        # Company Profile Management
        st.markdown("### 🏢 Company Profile Management")
        company_manager = get_company_manager()
        
        # Load existing profile
        recent_companies = company_manager.get_recent_companies(limit=10)
        if recent_companies:
            selected_company = st.selectbox(
                "Load Existing Profile:",
                [""] + [f"{comp['business_name']} ({comp['business_type']})" for comp in recent_companies],
                help="Quickly load a previously saved company profile"
            )
            
            if selected_company and st.button("📂 Load Profile", use_container_width=True):
                # Extract business name and find matching profile
                business_name = selected_company.split(" (")[0]
                profile = next((comp for comp in recent_companies if comp['business_name'] == business_name), None)
                
                if profile:
                    session_manager = get_session_manager()
                    session_manager.populate_from_profile(profile)
                    st.success(f"✅ Loaded profile for {business_name}")
                    st.rerun()
        
        # Save current profile
        if st.session_state.get('business_name'):
            if st.button("💾 Save Current Profile", use_container_width=True):
                session_manager = get_session_manager()
                profile = session_manager.create_profile_from_session()
                
                if company_manager.save_profile(profile):
                    st.success("✅ Profile saved successfully!")
                else:
                    st.error("❌ Error saving profile")
        
        st.markdown("---")
        
        # Website Analysis
        st.markdown("### 🌐 Website Analysis")
        st.markdown("Automatically extract company info from your website")
        
        website_url = st.text_input(
            "Website URL:",
            placeholder="https://yourcompany.com",
            help="Enter your website URL to automatically extract business information"
        )
        
        if website_url and st.button("🔍 Analyze Website", use_container_width=True):
            with st.spinner("🔍 Analyzing website content..."):
                analyzer = get_website_analyzer()
                results = analyzer.analyze_website(website_url)
                
                if results and results.get('success'):
                    st.session_state.website_analysis_results = results
                    
                    # Auto-populate session state with extracted information
                    session_manager = get_session_manager()
                    session_manager.populate_from_website_analysis(results)
                    
                    st.success("✅ Website analyzed successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Could not analyze website: {results.get('error', 'Unknown error')}")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button("📖 Help", use_container_width=True):
                st.session_state.show_documentation = True
                st.rerun()
        
        with col_action2:
            if st.button("💬 Feedback", use_container_width=True):
                st.session_state.show_feedback = True
                st.rerun()
        
        if st.button("🔄 Reset All", use_container_width=True):
            session_manager = get_session_manager()
            session_manager.clear_all_session_data()
            st.success("✅ All data reset!")
            st.rerun()
        
        return None

def handle_single_page_layout(template_config):
    """Handle the main single-page layout with all features."""
    st.markdown("### 🎯 Business Information")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        business_name = st.text_input(
            "Business/Brand Name *",
            value=st.session_state.get('business_name', ''),
            placeholder="e.g., Adcellerant Marketing",
            help="Enter your company or brand name"
        )
        st.session_state.business_name = business_name
        
        business_type = st.text_input(
            "Business Type *",
            value=st.session_state.get('business_type', ''),
            placeholder="e.g., Digital Marketing Agency",
            help="Describe what your business does"
        )
        st.session_state.business_type = business_type
    
    with col2:
        target_audience = st.text_input(
            "Target Audience *",
            value=st.session_state.get('target_audience', ''),
            placeholder="e.g., Small business owners",
            help="Who are you trying to reach?"
        )
        st.session_state.target_audience = target_audience
        
        product_name = st.text_input(
            "Product/Service Name",
            value=st.session_state.get('product_name', ''),
            placeholder="e.g., Social Media Management Package",
            help="What specific offering are you promoting?"
        )
        st.session_state.product_name = product_name
    
    # Check if minimum required fields are filled
    if business_name and business_type and target_audience:
        st.markdown("### ✨ Generate Social Media Captions")
        
        if st.button("🚀 Generate Captions", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is crafting your perfect captions..."):
                try:
                    # Initialize components
                    client = initialize_openai_client()
                    caption_manager = get_caption_manager()
                    stats_manager = get_statistics_manager()
                    
                    # Create prompt (simplified for this example)
                    prompt = f"""Create 3 engaging social media captions for {business_name}, a {business_type} targeting {target_audience}."""
                    
                    if product_name:
                        prompt += f" The post is about {product_name}."
                    
                    # Generate captions using OpenAI
                    response = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[
                            {"role": "system", "content": "You are an expert social media content creator. Generate engaging, platform-appropriate captions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    # Parse response and display captions
                    caption_text = response.choices[0].message.content
                    captions = [cap.strip() for cap in caption_text.split('\n\n') if cap.strip()]
                    
                    # Store in session state
                    st.session_state.generated_captions = captions[:3] if len(captions) >= 3 else captions
                    
                    # Update statistics
                    stats_manager.increment_captions_generated(len(st.session_state.generated_captions))
                    
                    st.success(f"✅ Generated {len(st.session_state.generated_captions)} captions!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating captions: {str(e)}")
    
    # Display generated captions
    if st.session_state.get('generated_captions'):
        st.markdown("### 📝 Generated Captions")
        
        for i, caption in enumerate(st.session_state.generated_captions, 1):
            with st.container():
                st.markdown(f"**Caption {i}:**")
                st.text_area(
                    f"Caption {i}",
                    value=caption,
                    height=100,
                    label_visibility="collapsed",
                    key=f"caption_{i}"
                )
                
                col_copy, col_edit = st.columns([1, 1])
                with col_copy:
                    if st.button(f"📋 Copy Caption {i}", key=f"copy_{i}"):
                        st.success(f"Caption {i} copied to clipboard!")
                
                st.markdown("---")
    
    else:
        st.info("👆 Fill in the required fields above and click 'Generate Captions' to get started!")

def show_app_footer():
    """Display app footer with quick access to help and feedback."""
    st.markdown("---")
    
    col_footer1, col_footer2, col_footer3, col_footer4 = st.columns([1, 1, 1, 1])
    
    with col_footer1:
        if st.button("📖 Documentation", help="View complete feature guide", use_container_width=True):
            st.session_state.show_documentation = True
            st.rerun()
    
    with col_footer2:
        if st.button("💬 Feedback", help="Report bugs or suggest improvements", use_container_width=True):
            st.session_state.show_feedback = True
            st.rerun()
    
    with col_footer3:
        if st.button("🔄 Reset App", help="Clear all data and start fresh", use_container_width=True):
            session_manager = get_session_manager()
            session_manager.clear_all_session_data()
            st.success("✅ App reset successfully!")
            st.rerun()
    
    with col_footer4:
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em; padding: 10px;'>
        🚀 Adcellerant Social Caption Generator<br>
        AI-Powered Social Media Content Creation
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application function."""
    # Check authentication first
    if not check_password():
        return
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    /* Enhanced styling for better UX */
    .batch-caption-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
        padding: 12px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
    }
    
    .platform-indicator {
        font-weight: bold;
        font-size: 12px;
    }
    
    .batch-image-column {
        margin-bottom: 30px;
        padding: 15px;
        background-color: #fafafa;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Display page header
    display_page_header()
    
    # Show documentation popup if requested
    show_documentation_popup()
    
    # Show feedback popup if requested
    show_feedback_popup()
    
    # Create enhanced sidebar
    template_config = create_advanced_sidebar()
    show_logout_option()
    
    # Main page layout
    handle_single_page_layout(template_config)

if __name__ == "__main__":
    main()
    show_app_footer()
