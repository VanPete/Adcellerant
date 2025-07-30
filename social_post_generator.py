#!/usr/bin/env python3
"""
Adcellerant Social Caption Generator
AI-Powered Social Media Caption Generator with Advanced Website Analysis

Author: Adcellerant Team
Version: 2.0
Last Updated: January 2025
Git Push Test: Verified virtual environment setup
"""

# Standard library imports
import base64
import csv
import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timedelta

# Third-party imports
import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from urllib.parse import urljoin, urlparse

# === Constants ===
# Data file configurations - These files persist across all users and sessions
COMPANY_DATA_FILE = "company_profiles.json"  # Shared company directory across all users
USED_CAPTIONS_FILE = "used_captions.json" 
FEEDBACK_FILE = "user_feedback.json"
STATS_FILE = "app_statistics.json"

# Security configuration  
APP_PASSWORD = os.getenv("APP_PASSWORD", "adcellerant2025")

# Feature flags - clipboard functionality removed for cleaner UI
CLIPBOARD_FEATURES_ENABLED = False

# === Page Configuration ===
st.set_page_config(
    page_title="🚀 Adcellerant Social Caption Generator",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Initialize OpenAI Client ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

@st.cache_resource
def init_openai_client():
    """Initialize OpenAI client with error handling."""
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        st.stop()
    return OpenAI(api_key=api_key)

client = init_openai_client()

# === Authentication Functions ===
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.markdown("## 🔐 Access Required")
        st.info("This application requires a password to access. Please contact Maddie Stitt for access.")
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Enter the application password"
        )
        
        # Add some styling
        st.markdown("""
        <style>
        .password-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 50vh;
        }
        </style>
        """, unsafe_allow_html=True)
        
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.markdown("## 🔐 Access Required")
        st.error("❌ Incorrect password. Please try again.")
        st.info("This application requires a password to access. Please contact Maddie Stitt for access.")
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Enter the application password"
        )
        return False
    else:
        # Password correct.
        return True

def show_logout_option():
    """Show logout option in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔓 Session")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            # Clear only authentication-related session state
            # Company directory and other persistent data remain intact
            auth_keys_to_clear = [
                'password_correct', 'password', 'current_image', 'generated_captions', 
                'website_analysis', 'selected_web_image', 'auto_business', 
                'selected_company_profile', 'selected_company_name', 'editing_company', 
                'editing_profile', 'show_save_options', 'show_documentation', 
                'show_feedback', 'image_selection_mode', 'clipboard_image', 'uploaded_image'
            ]
            
            for key in auth_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# === Caption Tracking System ===
def load_used_captions():
    """Load used captions from JSON file."""
    try:
        if os.path.exists(USED_CAPTIONS_FILE):
            with open(USED_CAPTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    except (PermissionError, OSError) as e:
        st.error(f"File access error loading used captions: {str(e)}")
        return {}

def save_used_captions(used_captions):
    """Save used captions to JSON file."""
    try:
        with open(USED_CAPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(used_captions, f, indent=2, ensure_ascii=False)
        return True
    except (PermissionError, OSError) as e:
        st.error(f"File access error saving used captions: {str(e)}")
        return False
    except (TypeError, ValueError) as e:
        st.error(f"Data serialization error: {str(e)}")
        return False

def mark_caption_as_used(caption_text, business_name=""):
    """Mark a caption as used."""
    import hashlib
    
    # Create a hash of the caption for comparison
    caption_hash = hashlib.md5(caption_text.strip().lower().encode()).hexdigest()
    
    used_captions = load_used_captions()
    timestamp = datetime.now().isoformat()
    
    used_captions[caption_hash] = {
        'text': caption_text.strip(),
        'business': business_name,
        'used_date': timestamp,
        'usage_count': used_captions.get(caption_hash, {}).get('usage_count', 0) + 1
    }
    
    save_used_captions(used_captions)

def unmark_caption_as_used(caption_text):
    """Remove a caption from the used captions history."""
    import hashlib
    
    # Create a hash of the caption for comparison
    caption_hash = hashlib.md5(caption_text.strip().lower().encode()).hexdigest()
    
    used_captions = load_used_captions()
    
    if caption_hash in used_captions:
        del used_captions[caption_hash]
        save_used_captions(used_captions)
        return True
    
    return False

def is_caption_duplicate(caption_text, threshold=0.8):
    """Check if a caption is too similar to previously used captions."""
    import hashlib
    
    caption_hash = hashlib.md5(caption_text.strip().lower().encode()).hexdigest()
    used_captions = load_used_captions()
    
    # Exact match
    if caption_hash in used_captions:
        return True, used_captions[caption_hash]
    
    # Similarity check (basic word overlap)
    new_words = set(caption_text.lower().split())
    
    for stored_hash, stored_data in used_captions.items():
        stored_words = set(stored_data['text'].lower().split())
        
        if len(new_words) > 0 and len(stored_words) > 0:
            overlap = len(new_words.intersection(stored_words))
            similarity = overlap / max(len(new_words), len(stored_words))
            
            if similarity >= threshold:
                return True, stored_data
    
    return False, None

def get_caption_usage_stats():
    """Get statistics about caption usage."""
    used_captions = load_used_captions()
    
    stats = {
        'total_used': len(used_captions),
        'recent_used': 0,
        'most_used_business': 'N/A'
    }
    
    if used_captions:
        # Count recent usage (last 7 days)
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        
        recent_count = 0
        business_counts = {}
        
        for caption_data in used_captions.values():
            try:
                used_date = datetime.fromisoformat(caption_data['used_date'])
                if used_date >= week_ago:
                    recent_count += 1
                
                business = caption_data.get('business', 'Unknown')
                business_counts[business] = business_counts.get(business, 0) + 1
            except:
                continue
        
        stats['recent_used'] = recent_count
        if business_counts:
            stats['most_used_business'] = max(business_counts, key=business_counts.get)
    
    return stats

def search_used_captions(search_query="", business_filter="", date_filter=""):
    """Search used captions with filters."""
    used_captions = load_used_captions()
    results = []
    
    for caption_hash, caption_data in used_captions.items():
        caption_text = caption_data.get('text', '')
        business = caption_data.get('business', '')
        used_date = caption_data.get('used_date', '')
        
        # Apply filters
        if search_query and search_query.lower() not in caption_text.lower():
            continue
            
        if business_filter and business_filter.lower() not in business.lower():
            continue
            
        if date_filter:
            try:
                caption_date = datetime.fromisoformat(used_date).date()
                filter_date = datetime.fromisoformat(date_filter).date()
                if caption_date != filter_date:
                    continue
            except:
                continue
        
        results.append({
            'hash': caption_hash,
            'text': caption_text,
            'business': business,
            'used_date': used_date,
            'usage_count': caption_data.get('usage_count', 1)
        })
    
    # Sort by most recent first
    results.sort(key=lambda x: x['used_date'], reverse=True)
    return results

def get_unique_businesses():
    """Get list of unique businesses from used captions."""
    used_captions = load_used_captions()
    businesses = set()
    
    for caption_data in used_captions.values():
        business = caption_data.get('business', '').strip()
        if business:
            businesses.add(business)
    
    return sorted(list(businesses))

def delete_multiple_captions(caption_hashes):
    """Delete multiple captions from usage history."""
    if not caption_hashes:
        return False
        
    used_captions = load_used_captions()
    deleted_count = 0
    
    for caption_hash in caption_hashes:
        if caption_hash in used_captions:
            del used_captions[caption_hash]
            deleted_count += 1
    
    if deleted_count > 0:
        save_used_captions(used_captions)
        return deleted_count
    
    return 0

def export_caption_history():
    """Export caption history to CSV format."""
    used_captions = load_used_captions()
    
    if not used_captions:
        return None
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Caption Text', 'Business', 'Used Date', 'Usage Count'])
    
    # Write data
    for caption_data in used_captions.values():
        writer.writerow([
            caption_data.get('text', ''),
            caption_data.get('business', ''),
            caption_data.get('used_date', ''),
            caption_data.get('usage_count', 1)
        ])
    
    return output.getvalue()

# === Feedback & Statistics Tracking System ===
def load_feedback_submissions():
    """Load feedback submissions from JSON file."""
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return []
    except Exception as e:
        st.error(f"Error loading feedback: {str(e)}")
        return []

def save_feedback_submission(feedback_data):
    """Save feedback submission to JSON file."""
    try:
        feedback_list = load_feedback_submissions()
        
        # Add timestamp and ID
        feedback_data.update({
            'submission_date': datetime.now().isoformat(),
            'id': len(feedback_list) + 1
        })
        
        feedback_list.append(feedback_data)
        
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedback_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving feedback: {str(e)}")
        return False

def load_app_statistics():
    """Load app statistics from JSON file."""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'total_captions_generated': 0,
            'total_sessions': 0,
            'first_use_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {
            'total_captions_generated': 0,
            'total_sessions': 0,
            'first_use_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        return {
            'total_captions_generated': 0,
            'total_sessions': 0,
            'first_use_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

def save_app_statistics(stats):
    """Save app statistics to JSON file."""
    try:
        stats['last_updated'] = datetime.now().isoformat()
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving statistics: {str(e)}")
        return False

def increment_captions_generated(count=3):
    """Increment the total captions generated counter."""
    stats = load_app_statistics()
    stats['total_captions_generated'] += count
    save_app_statistics(stats)
    return stats['total_captions_generated']

def get_feedback_summary():
    """Get summary of feedback submissions."""
    feedback_list = load_feedback_submissions()
    
    if not feedback_list:
        return {
            'total': 0,
            'bug_reports': 0,
            'feature_requests': 0,
            'general_feedback': 0,
            'questions': 0,
            'recent': 0
        }
    
    # Count by type
    type_counts = {
        'bug_reports': 0,
        'feature_requests': 0,
        'general_feedback': 0,
        'questions': 0
    }
    
    recent_count = 0
    week_ago = datetime.now() - timedelta(days=7)
    
    for feedback in feedback_list:
        feedback_type = feedback.get('type', '').lower()
        if 'bug' in feedback_type:
            type_counts['bug_reports'] += 1
        elif 'feature' in feedback_type:
            type_counts['feature_requests'] += 1
        elif 'question' in feedback_type or 'support' in feedback_type:
            type_counts['questions'] += 1
        else:
            type_counts['general_feedback'] += 1
        
        # Count recent submissions
        try:
            submission_date = datetime.fromisoformat(feedback.get('submission_date', ''))
            if submission_date >= week_ago:
                recent_count += 1
        except:
            continue
    
    return {
        'total': len(feedback_list),
        'recent': recent_count,
        **type_counts
    }

def export_feedback_data():
    """Export feedback data to CSV format."""
    feedback_list = load_feedback_submissions()
    
    if not feedback_list:
        return None
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['ID', 'Type', 'Severity', 'Description', 'Steps', 'Browser', 'Email', 'Name', 'Submission Date'])
    
    # Write data
    for feedback in feedback_list:
        writer.writerow([
            feedback.get('id', ''),
            feedback.get('type', ''),
            feedback.get('severity', ''),
            feedback.get('description', ''),
            feedback.get('steps', ''),
            feedback.get('browser_info', ''),
            feedback.get('email', ''),
            feedback.get('name', ''),
            feedback.get('submission_date', '')
        ])
    
    return output.getvalue()

# === Company Directory Management ===
# NOTE: Company profiles are stored persistently in JSON files and shared across ALL users.
# This data persists across sessions, logouts, and app restarts.
def load_company_profiles():
    """Load saved company profiles from JSON file with error handling.
    
    Company profiles are shared across all users and persist across sessions.
    """
    try:
        if os.path.exists(COMPANY_DATA_FILE):
            with open(COMPANY_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        st.error(f"Error loading company profiles: {str(e)}")
        return {}
    except (PermissionError, OSError) as e:
        st.error(f"File access error loading company profiles: {str(e)}")
        return {}

def save_company_profiles(profiles):
    """Save company profiles to JSON file with error handling.
    
    Company profiles are shared across all users and persist across sessions.
    """
    try:
        with open(COMPANY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving company profiles: {str(e)}")
        return False

def save_company_profile(company_name, profile_data):
    """Save a single company profile with timestamp tracking.
    
    Company profiles are shared across all users and persist across sessions.
    """
    if not company_name or not profile_data:
        return False
        
    profiles = load_company_profiles()
    
    # Add timestamps for tracking
    profile_data.update({
        'saved_date': datetime.now().isoformat(),
        'last_used': datetime.now().isoformat()
    })
    
    profiles[company_name] = profile_data
    return save_company_profiles(profiles)

def get_company_profile(company_name):
    """Get a specific company profile and update last used timestamp."""
    if not company_name:
        return None
        
    profiles = load_company_profiles()
    if company_name in profiles:
        # Update last used timestamp
        profiles[company_name]['last_used'] = datetime.now().isoformat()
        save_company_profiles(profiles)
        return profiles[company_name]
    return None

def delete_company_profile(company_name):
    """Delete a company profile from storage."""
    if not company_name:
        return False
        
    profiles = load_company_profiles()
    if company_name in profiles:
        del profiles[company_name]
        return save_company_profiles(profiles)
    return False

def create_profile_data_from_settings(settings):
    """Create standardized profile data dictionary from current settings.
    
    Args:
        settings (dict): Current session settings dictionary
        
    Returns:
        dict: Standardized profile data with all required fields
    """
    return {
        'business_input': settings.get('business_input', ''),
        'website_url': settings.get('website_url', ''),
        'caption_style': settings.get('caption_style', 'Professional'),
        'caption_length': settings.get('caption_length', 'Medium (4-6 sentences)'),
        'use_premium_model': settings.get('use_premium_model', False),
        'include_cta': settings.get('include_cta', True),
        'focus_keywords': settings.get('focus_keywords', ''),
        'avoid_words': settings.get('avoid_words', ''),
        'target_audience': settings.get('target_audience', 'General'),
        'text_only_mode': settings.get('text_only_mode', False),
        'character_limit_preference': settings.get('character_limit_preference', 'No limit'),
        'captions_generated_count': 1,
        'website_analysis': st.session_state.get('website_analysis')
    }

def clear_all_session_data():
    """Clear all session state data for starting over."""
    keys_to_clear = [
        'current_image', 'generated_captions', 'website_analysis', 
        'selected_web_image', 'auto_business', 'selected_company_profile',
        'selected_company_name', 'editing_company', 'editing_profile', 
        'show_save_options', 'show_documentation', 'show_feedback',
        'image_selection_mode', 'clipboard_image', 'uploaded_image'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear cached data
    st.cache_data.clear()

# === Website Analysis Functions ===
@st.cache_data(ttl=300, show_spinner=False)
def analyze_website(url):
    """Extract key information from a company's website including multiple pages."""
    if not url:
        return None
    
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        base_domain = url.split('/')[2]
        
        # Fetch main page
        main_response = _fetch_page_with_retries(url)
        if not main_response:
            raise Exception("Failed to fetch main page after trying multiple approaches")
        
        main_soup = BeautifulSoup(main_response.content, 'html.parser')
        
        # Get priority pages to analyze
        priority_pages = _discover_priority_pages(url, base_domain, main_soup)
        
        # Initialize analysis structure
        analysis = _initialize_analysis(main_soup, url)
        
        # Fetch and analyze all pages
        all_soups = [main_soup]
        for page_url in priority_pages:
            try:
                page_response = _fetch_page_with_retries(page_url)
                if page_response:
                    page_soup = BeautifulSoup(page_response.content, 'html.parser')
                    all_soups.append(page_soup)
                    analysis['pages_analyzed'].append(page_url)
            except Exception:
                continue
        
        # Extract and process content from all pages
        analysis.update(_extract_content_from_pages(all_soups))
        
        # Extract images from main page
        analysis['images'] = extract_website_images(url, main_soup)
        
        return analysis
        
    except Exception as e:
        _handle_website_analysis_error(e, url)
        return None

def _fetch_page_with_retries(page_url):
    """Fetch a page with multiple user agent retries."""
    headers_list = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        }
    ]
    
    for headers in headers_list:
        try:
            response = requests.get(page_url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response and response.status_code == 403:
                continue  # Try next headers
            else:
                raise
        except Exception:
            continue
    
    return None

def _discover_priority_pages(url, base_domain, main_soup):
    """Discover and score priority pages for analysis."""
    page_scores = {}
    links = main_soup.find_all('a', href=True)
    
    # Define keywords for scoring
    high_priority_keywords = [
        'about', 'company', 'mission', 'vision', 'story', 'history', 'who-we-are', 
        'our-team', 'leadership', 'founders', 'values', 'culture'
    ]
    medium_priority_keywords = [
        'service', 'product', 'offering', 'solution', 'what-we-do', 'expertise', 
        'specialties', 'capabilities', 'features', 'portfolio', 'work'
    ]
    low_priority_keywords = [
        'team', 'staff', 'experience', 'case-studies', 'testimonials', 
        'reviews', 'clients', 'projects', 'gallery', 'showcase'
    ]
    nav_patterns = [
        'about us', 'our services', 'what we do', 'our company', 'our story',
        'meet the team', 'our mission', 'company info', 'get to know us',
        'our expertise', 'why choose us', 'our approach', 'company profile'
    ]
    
    for link in links[:150]:
        href = link.get('href', '').lower()
        link_text = link.get_text(strip=True).lower()
        
        # Convert to absolute URL
        if href.startswith('/'):
            full_url = f"{url.rstrip('/')}{href}"
        elif href.startswith('http') and base_domain in href:
            full_url = href
        else:
            continue
        
        # Skip unwanted patterns
        skip_patterns = ['#', 'mailto:', 'tel:', 'javascript:', '.pdf', '.jpg', '.png', '.gif', 
                       '.doc', '.docx', '.zip', '.csv', 'login', 'register', 'cart', 'checkout',
                       'privacy', 'terms', 'cookie', 'sitemap.xml', '.xml', 'feed', 'rss']
        if any(skip in href for skip in skip_patterns):
            continue
        
        # Calculate score
        score = 0
        
        # URL keyword scoring
        for keyword in high_priority_keywords:
            if keyword in href:
                score += 15
        for keyword in medium_priority_keywords:
            if keyword in href:
                score += 10
        for keyword in low_priority_keywords:
            if keyword in href:
                score += 7
        
        # Link text scoring
        for keyword in high_priority_keywords:
            if keyword in link_text:
                score += 12
        for keyword in medium_priority_keywords:
            if keyword in link_text:
                score += 8
        for keyword in low_priority_keywords:
            if keyword in link_text:
                score += 5
        
        # Navigation pattern bonus
        for pattern in nav_patterns:
            if pattern in link_text:
                score += 20
        
        # Depth bonus (prefer shallow pages)
        depth = href.count('/')
        if depth <= 3:
            score += 5
        elif depth <= 5:
            score += 2
        
        if score > 0 and full_url not in page_scores:
            page_scores[full_url] = score
    
    # Return top 10 pages
    sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
    return [page[0] for page in sorted_pages[:10]]

def _initialize_analysis(main_soup, url):
    """Initialize the analysis structure with main page data."""
    analysis = {
        'title': main_soup.find('title').get_text() if main_soup.find('title') else '',
        'description': '',
        'keywords': '',
        'about_text': '',
        'services': [],
        'tone': 'professional',
        'pages_analyzed': [url]
    }
    
    # Get meta description
    meta_desc = main_soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        analysis['description'] = meta_desc.get('content', '')
    
    # Get meta keywords
    meta_keywords = main_soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords:
        analysis['keywords'] = meta_keywords.get('content', '')
    
    return analysis

def _extract_content_from_pages(all_soups):
    """Extract and process content from all analyzed pages."""
    all_about_text = []
    all_services = []
    
    for soup in all_soups:
        # Extract about text
        about_sections = soup.find_all(['div', 'section', 'p', 'h1', 'h2', 'h3', 'article'], 
            class_=lambda x: x and any(
                word in x.lower() for word in ['about', 'mission', 'vision', 'story', 'who-we-are', 'company', 'intro', 'overview']
            ))
        
        # Also check by ID
        about_sections.extend(soup.find_all(['div', 'section'], 
            id=lambda x: x and any(
                word in x.lower() for word in ['about', 'mission', 'vision', 'story', 'company']
            )))
        
        # Main content areas
        main_content = soup.find_all(['main', 'article', '.content', '.main-content'])
        if main_content:
            about_sections.extend(main_content)
        
        # Process about text
        page_about_text = []
        for section in about_sections[:8]:
            text = section.get_text(strip=True)
            if len(text) > 50 and not any(skip in text.lower() for skip in ['cookie', 'privacy', 'terms', 'menu', 'navigation']):
                page_about_text.append(text)
        
        combined_text = ' '.join(page_about_text)
        if combined_text and len(combined_text) > 30:
            all_about_text.append(combined_text)
        
        # Extract services
        service_sections = soup.find_all(['div', 'section', 'li', 'h2', 'h3', 'h4', 'article'], 
            class_=lambda x: x and any(
                word in x.lower() for word in ['service', 'product', 'offering', 'solution', 'feature', 'specialty', 'expertise']
            ))
        
        service_lists = soup.find_all(['ul', 'ol'], class_=lambda x: x and 'service' in x.lower())
        service_sections.extend(service_lists)
        
        page_services = []
        for section in service_sections[:12]:
            text = section.get_text(strip=True)
            if 15 < len(text) < 200:
                page_services.append(text)
        
        all_services.extend(page_services)
    
    # Process and deduplicate content
    return {
        'about_text': _process_about_text(all_about_text),
        'services': _process_services(all_services)
    }

def _process_about_text(all_about_text):
    """Process and deduplicate about text."""
    unique_about_texts = []
    seen_phrases = []
    
    for text in all_about_text:
        words = text.lower().split()
        if len(words) > 10:
            overlap = False
            for seen_words in seen_phrases:
                words_set = set(words)
                seen_set = set(seen_words)
                if len(words_set.intersection(seen_set)) / len(words_set) > 0.7:
                    overlap = True
                    break
            
            if not overlap:
                unique_about_texts.append(text)
                seen_phrases.append(words)
    
    return ' '.join(unique_about_texts)[:1200]

def _process_services(all_services):
    """Process and deduplicate services."""
    clean_services = []
    for service in all_services:
        if not any(skip in service.lower() for skip in ['read more', 'learn more', 'contact', 'click here', 'view all']):
            clean_services.append(service)
    
    # Remove duplicates while preserving order
    seen_services = []
    unique_services = []
    for service in clean_services:
        service_lower = service.lower()
        if service_lower not in seen_services:
            seen_services.append(service_lower)
            unique_services.append(service)
    
    return unique_services[:15]

def _handle_website_analysis_error(error, url):
    """Handle and display appropriate error messages for website analysis failures."""
    error_msg = str(error)
    if "403" in error_msg and "Forbidden" in error_msg:
        st.warning(f"⚠️ Website access blocked: {url}")
        st.info("💡 The website is blocking automated access. You can still use the tool by:")
        st.info("• Entering just the business type/name")
        st.info("• Using uploaded images or clipboard images")
        st.info("• The captions will still be generated, just without website-specific context")
    elif "404" in error_msg:
        st.warning(f"⚠️ Website not found: {url}")
        st.info("💡 Please check the URL and try again, or continue without website analysis")
    elif "timeout" in error_msg.lower():
        st.warning(f"⚠️ Website took too long to respond: {url}")
        st.info("💡 The website may be slow or temporarily unavailable")
    else:
        st.warning(f"⚠️ Could not analyze website: {error_msg}")
        st.info("💡 Continuing without website analysis - captions will still be generated")

def analyze_website_with_spinner(url):
    """Wrapper function to show spinner while analyzing website."""
    with st.spinner(f"🌐 Analyzing website: {url}"):
        return analyze_website(url)

# === Website Image Extraction ===
@st.cache_data(ttl=300)
def extract_website_images(base_url, _soup):
    """Extract relevant images from website for potential social media use."""
    if not base_url or not _soup:
        return []
        
    try:
        images = []
        img_tags = _soup.find_all('img')
        
        # Process up to 10 images to avoid excessive processing
        for img in img_tags[:10]:
            processed_image = _process_image_tag(img, base_url)
            if processed_image:
                images.append(processed_image)
        
        return images[:5]  # Return top 5 suitable images
        
    except Exception as e:
        st.warning(f"⚠️ Error extracting website images: {str(e)}")
        return []

def _process_image_tag(img, base_url):
    """Process a single image tag and return image info if suitable."""
    # Get image source
    src = img.get('src') or img.get('data-src')
    if not src:
        return None
    
    # Convert to absolute URL
    src = _normalize_image_url(src, base_url)
    if not src:
        return None
    
    # Filter out unwanted images
    if _should_skip_image(src):
        return None
    
    # Check image dimensions
    if not _has_suitable_dimensions(img):
        return None
    
    # Extract image metadata
    alt_text = img.get('alt', '')
    title = img.get('title', '')
    description = alt_text or title or 'Website image'
    
    return {
        'url': src,
        'alt': alt_text,
        'title': title,
        'description': description
    }

def _normalize_image_url(src, base_url):
    """Normalize image URL to absolute format."""
    if src.startswith('//'):
        return 'https:' + src
    elif src.startswith('/'):
        return urljoin(base_url, src)
    elif not src.startswith(('http://', 'https://')):
        return urljoin(base_url, src)
    return src

def _should_skip_image(src):
    """Check if image should be skipped based on URL patterns."""
    skip_patterns = ['logo', 'icon', 'favicon', 'avatar', 'thumb', 'badge', 'button']
    return any(skip in src.lower() for skip in skip_patterns)

def _has_suitable_dimensions(img):
    """Check if image has suitable dimensions for social media."""
    width = img.get('width')
    height = img.get('height')
    
    if width and height:
        try:
            w, h = int(width), int(height)
            # Skip very small images (likely icons/thumbnails)
            return w >= 200 and h >= 200
        except ValueError:
            pass  # Invalid dimensions, continue processing
    
    return True  # Allow images without specified dimensions

# === Caption Generation Functions ===
def generate_captions(image_data, business_input, website_url, use_premium_model=False, 
                     caption_style="Professional", include_cta=True, 
                     caption_length="Medium (4-6 sentences)", text_only_mode=False,
                     character_limit_preference="No limit"):
    """Main function to generate social media captions."""
    try:
        # Analyze website if URL provided
        website_info = _get_website_info(website_url)
        
        # Create prompt based on available information
        prompt = _create_caption_prompt(
            website_info, business_input, caption_style, 
            caption_length, include_cta, text_only_mode, character_limit_preference
        )
        
        # Generate captions using OpenAI
        result = _generate_with_openai(
            prompt, image_data, use_premium_model, text_only_mode
        )
        
        # Display analysis summary if available
        _display_analysis_summary(website_info, website_url)
        
        return result
        
    except Exception as e:
        _handle_caption_generation_error(e)
        return None

def _get_website_info(website_url):
    """Get website information if URL is provided."""
    if website_url and website_url.strip():
        return analyze_website_with_spinner(website_url.strip())
    return None

def _create_caption_prompt(website_info, business_input, caption_style, 
                          caption_length, include_cta, text_only_mode, character_limit_preference="No limit"):
    """Create the prompt for caption generation based on available information."""
    # Style and length mappings
    style_instructions = _get_style_instructions()
    length_map = _get_length_mapping()
    
    cta_instruction = _get_cta_instruction(include_cta)
    
    if website_info and isinstance(website_info, dict):
        return _create_enhanced_prompt(
            website_info, business_input, style_instructions, 
            length_map, caption_style, caption_length, 
            cta_instruction, text_only_mode, character_limit_preference
        )
    else:
        return _create_basic_prompt(
            business_input, style_instructions, length_map, 
            caption_style, caption_length, cta_instruction, text_only_mode, character_limit_preference
        )

def _get_style_instructions():
    """Get style instruction mappings."""
    return {
        "Professional": "maintaining a professional, trustworthy tone",
        "Casual & Friendly": "using a warm, conversational, and approachable tone",
        "Inspirational": "focusing on motivation, dreams, and positive transformation",
        "Educational": "providing valuable insights and information",
        "Promotional": "highlighting benefits and encouraging action"
    }

def _get_length_mapping():
    """Get length mapping for captions."""
    return {
        "Short (3-4 sentences)": "3-4 sentences",
        "Medium (4-6 sentences)": "4-6 sentences", 
        "Long (6+ sentences)": "6 or more sentences"
    }

def _get_cta_instruction(include_cta):
    """Get call-to-action instruction."""
    return ("Include a subtle call-to-action that encourages engagement." 
            if include_cta else "Focus on storytelling without direct calls-to-action.")

def _get_character_limit_instruction(character_limit_preference):
    """Get character limit instruction for prompt."""
    if character_limit_preference == "No limit":
        return "Ready for Instagram, Facebook, or LinkedIn"
    
    char_limits = {
        "Facebook (≤500 chars)": "- IMPORTANT: Each caption must be 500 characters or less for Facebook optimization",
        "Instagram (≤400 chars)": "- IMPORTANT: Each caption must be 400 characters or less for Instagram optimization", 
        "LinkedIn (≤700 chars)": "- IMPORTANT: Each caption must be 700 characters or less for LinkedIn optimization",
        "Twitter/X (≤280 chars)": "- IMPORTANT: Each caption must be 280 characters or less for Twitter/X compatibility",
        "All platforms (≤280 chars)": "- IMPORTANT: Each caption must be 280 characters or less for universal platform compatibility"
    }
    
    return char_limits.get(character_limit_preference, "Ready for Instagram, Facebook, or LinkedIn")

def _create_enhanced_prompt(website_info, business_input, style_instructions, 
                           length_map, caption_style, caption_length, 
                           cta_instruction, text_only_mode, character_limit_preference="No limit"):
    """Create enhanced prompt using website information."""
    company_name = website_info.get('title', business_input).split('|')[0].strip()
    company_description = website_info.get('description', '')
    services = ', '.join(website_info.get('services', [])[:3])
    about_text = website_info.get('about_text', '')
    
    # Get character limit instruction
    char_limit_instruction = _get_character_limit_instruction(character_limit_preference)
    
    base_requirements = f"""Requirements:
- Each caption should be exactly {length_map[caption_length]} long
- NO emojis or hashtags
- Style: {style_instructions[caption_style]}
- {char_limit_instruction}
- {cta_instruction}
- Focus on connecting with the audience through authentic storytelling"""
    
    company_info = f"""Company Information:
- Business Type: {business_input}
- Description: {company_description}
- Services: {services}
- About: {about_text[:200]}"""
    
    if text_only_mode:
        return f"""Create 3 engaging social media captions for {company_name} based on the company information provided (no image reference needed).

{company_info}

{base_requirements} about the business

Format as 3 separate captions, each on its own paragraph:

[First caption without emojis/hashtags]

[Second caption without emojis/hashtags]

[Third caption without emojis/hashtags]"""
    else:
        return f"""Create 3 engaging social media captions for {company_name} using the uploaded image.

{company_info}

{base_requirements}
- Reference the image content appropriately and naturally

Format as 3 separate captions, each on its own paragraph:

[First caption without emojis/hashtags]

[Second caption without emojis/hashtags]

[Third caption without emojis/hashtags]"""

def _create_basic_prompt(business_input, style_instructions, length_map, 
                        caption_style, caption_length, cta_instruction, text_only_mode, character_limit_preference="No limit"):
    """Create basic prompt without website information."""
    business_type = business_input if business_input.strip() else "business"
    
    # Get character limit instruction
    char_limit_instruction = _get_character_limit_instruction(character_limit_preference)
    
    base_requirements = f"""Requirements:
- Each caption should be exactly {length_map[caption_length]} long
- NO emojis or hashtags
- Style: {style_instructions[caption_style]}
- Include storytelling elements that connect with the audience
- {char_limit_instruction}
- {cta_instruction}"""
    
    if text_only_mode:
        return f"""Create 3 engaging social media captions for a {business_type} based on the business type provided.

{base_requirements}
- Create engaging content about typical {business_type} activities, values, or services

Format as 3 separate captions, each on its own paragraph:

[First caption without emojis/hashtags]

[Second caption without emojis/hashtags]

[Third caption without emojis/hashtags]"""
    else:
        return f"""Create 3 engaging social media captions for a {business_type} using this image.

{base_requirements}
- Reference the image content naturally

Format as 3 separate captions, each on its own paragraph:

[First caption without emojis/hashtags]

[Second caption without emojis/hashtags]

[Third caption without emojis/hashtags]"""

def _generate_with_openai(prompt, image_data, use_premium_model, text_only_mode):
    """Generate captions using OpenAI API with duplicate checking."""
    model = "gpt-4o" if use_premium_model else "gpt-4o-mini"
    
    max_attempts = 3
    duplicate_found = False
    
    with st.spinner(f"🤖 Generating {'text-only ' if text_only_mode else ''}captions using {model}..."):
        for attempt in range(max_attempts):
            if attempt > 0:
                # Add variety instruction for retry attempts
                enhanced_prompt = prompt + f"\n\n🔄 RETRY #{attempt + 1}: Create completely different, fresh captions that are unique and haven't been used before. Use different phrases, angles, and approaches."
            else:
                enhanced_prompt = prompt
            
            if text_only_mode:
                result = _generate_text_only(enhanced_prompt, model)
            else:
                result = _generate_with_image(enhanced_prompt, image_data, model)
            
            # Check for duplicates in the generated captions
            if result:
                captions = result.split('\n\n')
                duplicate_count = 0
                
                for caption in captions:
                    if caption.strip():
                        is_dup, _ = is_caption_duplicate(caption.strip())
                        if is_dup:
                            duplicate_count += 1
                
                # If less than half are duplicates, accept the result
                if duplicate_count < len([c for c in captions if c.strip()]) / 2:
                    if attempt > 0:
                        st.info(f"✨ Generated fresh captions on attempt {attempt + 1}")
                    return result
                else:
                    duplicate_found = True
                    if attempt < max_attempts - 1:
                        st.warning(f"🔄 Attempt {attempt + 1}: Some similar captions detected, generating alternatives...")
            
        # If we've tried multiple times and still have duplicates
        if duplicate_found:
            st.warning("⚠️ Some generated captions may be similar to previously used ones. Consider using different keywords or business descriptions for more variety.")
        
        return result

def _generate_text_only(prompt, model):
    """Generate text-only captions."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

def _generate_with_image(prompt, image_data, model):
    """Generate captions with image."""
    # Convert image to base64
    img_buffer = io.BytesIO()
    image_data.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    b64_image = base64.b64encode(img_buffer.read()).decode("utf-8")
    
    # Call GPT-4 with Vision
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}},
            ],
        }],
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

def _display_analysis_summary(website_info, website_url):
    """Display website analysis summary if available."""
    if website_info and isinstance(website_info, dict):
        company_name = website_info.get('title', 'Company').split('|')[0].strip()
        pages_analyzed = website_info.get('pages_analyzed', [])
        
        if len(pages_analyzed) > 1:
            st.success(f"✅ Website Analysis Complete for {company_name} ({len(pages_analyzed)} pages analyzed)")
            with st.expander("📄 Pages Analyzed"):
                for i, page in enumerate(pages_analyzed[:5], 1):
                    st.write(f"{i}. {page}")
        else:
            st.success(f"✅ Website Analysis Complete for {company_name}")
    elif website_url and website_url.strip():
        st.warning("⚠️ Website Analysis Failed - Using basic business type only")

def _handle_caption_generation_error(error):
    """Handle and display caption generation errors."""
    error_msg = str(error)
    
    error_mappings = {
        "429": ("⚠️ OpenAI API Quota Exceeded!", 
               "Please check your billing at: https://platform.openai.com/account/billing"),
        "401": ("🔑 Authentication Error", 
               "Please check your OpenAI API key in the .env file."),
        "403": ("🚫 Access Denied", 
               "Your API key doesn't have permission for this model."),
        "rate_limit": ("⏰ Rate Limit", 
                      "Too many requests. Please wait a moment and try again.")
    }
    
    for error_code, (title, message) in error_mappings.items():
        if error_code in error_msg.lower():
            st.error(f"{title}: {message}")
            return
    
    st.error(f"❌ Error generating captions: {error_msg}")

# === UI Helper Functions ===
def show_progress_indicator(step, total_steps, step_name):
    """Show progress indicator for multi-step processes."""
    progress = step / total_steps
    st.progress(progress)
    st.caption(f"Step {step}/{total_steps}: {step_name}")

# === Reusable UI Components ===
def create_header_with_close_button(title, close_key):
    """Create a standard header with title and close button layout.
    
    Args:
        title (str): The header title text
        close_key (str): Session state key to set when close button is clicked
        
    Returns:
        tuple: (title_column, close_column) for further customization
    """
    col_title, col_close = st.columns([4, 1])
    
    with col_title:
        st.markdown(f"### {title}")
    
    with col_close:
        if st.button("❌", key=f"close_{close_key}", help="Close"):
            st.session_state[close_key] = False
            st.rerun()
    
    return col_title, col_close

def create_caption_action_layout():
    """Create standard caption display layout with header and action columns.
    
    Returns:
        tuple: (header_column, action_column) for caption display
    """
    return st.columns([4, 1])

def create_bulk_action_layout():
    """Create standard bulk action button layout.
    
    Returns:
        tuple: (action_col1, action_col2) for bulk operations
    """
    return st.columns(2)

def create_download_action_layout():
    """Create standard download section with 4 equal columns.
    
    Returns:
        tuple: (col1, col2, col3, col4) for download options
    """
    return st.columns(4)

def create_config_display_layout():
    """Create standard configuration display with 2 equal columns.
    
    Returns:
        tuple: (config_col1, config_col2) for settings display
    """
    return st.columns(2)

def create_business_profile_template():
    """Create predefined business profile templates."""
    templates = {
        "Restaurant/Food Service": {
            "keywords": ["cuisine", "dining", "menu", "chef", "fresh", "local"],
            "tone": "Casual & Friendly",
            "cta_style": "Visit us today"
        },
        "Fitness/Health": {
            "keywords": ["fitness", "health", "training", "wellness", "strength"],
            "tone": "Inspirational", 
            "cta_style": "Start your journey"
        },
        "Professional Services": {
            "keywords": ["expertise", "solutions", "consulting", "professional"],
            "tone": "Professional",
            "cta_style": "Contact us today"
        },
        "Retail/E-commerce": {
            "keywords": ["products", "quality", "shopping", "collection"],
            "tone": "Promotional",
            "cta_style": "Shop now"
        },
        "Tech/Software": {
            "keywords": ["innovation", "technology", "solutions", "digital"],
            "tone": "Educational",
            "cta_style": "Learn more"
        }
    }
    return templates

def create_advanced_sidebar():
    """Create enhanced sidebar with better organization."""
    with st.sidebar:
        # Start Over Button - prominently placed at top
        st.markdown("### 🔄 Quick Actions")
        if st.button("🆕 Start Over", type="secondary", use_container_width=True, help="Clear all fields and start fresh"):
            clear_all_session_data()
            st.success("✅ All fields cleared!")
            st.rerun()
        
        st.markdown("---")
        
        # Company Directory Section
        st.markdown("### 🏢 Company Directory")
        
        company_profiles = load_company_profiles()
        
        if company_profiles:
            company_names = ["Select a saved company..."] + list(company_profiles.keys())
            selected_company = st.selectbox(
                "Load Saved Company",
                company_names,
                key="company_selector",
                help="Select a previously saved company to auto-fill information"
            )
            
            if selected_company != "Select a saved company...":
                if st.button("📋 Load Company Profile", use_container_width=True):
                    profile = get_company_profile(selected_company)
                    if profile:
                        # Store in session state for use in main tabs
                        st.session_state.selected_company_profile = profile
                        st.session_state.selected_company_name = selected_company
                        st.success(f"✅ Loaded profile for {selected_company}")
                        st.rerun()
            
            # Show company management
            with st.expander("📊 Manage Companies"):
                if company_profiles:
                    st.write(f"**Saved Companies:** {len(company_profiles)}")
                    
                    # Show recent companies
                    sorted_companies = sorted(
                        company_profiles.items(), 
                        key=lambda x: x[1].get('last_used', ''), 
                        reverse=True
                    )
                    
                    st.write("**Recently Used:**")
                    for company_name, profile in sorted_companies[:3]:
                        last_used = profile.get('last_used', 'Unknown')
                        if last_used != 'Unknown':
                            try:
                                last_used_date = datetime.fromisoformat(last_used).strftime("%m/%d/%Y")
                            except:
                                last_used_date = "Unknown"
                        else:
                            last_used_date = "Unknown"
                        st.write(f"• {company_name} (Last used: {last_used_date})")
                    
                    # Company management options
                    management_mode = st.radio(
                        "Management Options:",
                        ["None", "🗑️ Delete Company", "✏️ Edit Company"],
                        horizontal=True,
                        key="management_mode"
                    )
                    
                    if management_mode == "🗑️ Delete Company":
                        delete_company = st.selectbox(
                            "Select company to delete",
                            ["Select..."] + list(company_profiles.keys()),
                            key="delete_selector"
                        )
                        
                        if delete_company != "Select..." and st.button("🗑️ Delete", type="secondary"):
                            if delete_company_profile(delete_company):
                                st.success(f"✅ Deleted {delete_company}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete company")
                    
                    elif management_mode == "✏️ Edit Company":
                        edit_company = st.selectbox(
                            "Select company to edit",
                            ["Select..."] + list(company_profiles.keys()),
                            key="edit_selector"
                        )
                        
                        if edit_company != "Select...":
                            if st.button("✏️ Load for Editing", type="primary"):
                                profile = get_company_profile(edit_company)
                                if profile:
                                    # Store in session state for editing
                                    st.session_state.editing_company = edit_company
                                    st.session_state.editing_profile = profile
                                    st.session_state.selected_company_profile = profile
                                    st.session_state.selected_company_name = edit_company
                                    st.success(f"✅ Loaded {edit_company} for editing. Update the information in the tabs and save with a new name or overwrite the existing profile.")
                                    st.rerun()
                            
                            # Show save button if company is currently being edited
                            if (st.session_state.get('editing_company') == edit_company and 
                                st.session_state.get('selected_company_profile')):
                                if st.button("💾 Save Changes", type="secondary"):
                                    try:
                                        # Collect current settings from session state
                                        current_settings = {
                                            'business_input': st.session_state.get('temp_business_input', ''),
                                            'website_url': st.session_state.get('temp_website_url', ''),
                                            'caption_style': st.session_state.get('temp_caption_style', 'Professional'),
                                            'caption_length': st.session_state.get('temp_caption_length', 'Medium (4-6 sentences)'),
                                            'use_premium_model': st.session_state.get('temp_use_premium_model', False),
                                            'include_cta': st.session_state.get('temp_include_cta', True),
                                            'character_limit_preference': st.session_state.get('temp_character_limit_preference', 'No limit')
                                        }
                                        
                                        # Create updated profile from current settings
                                        updated_profile = create_profile_data_from_settings(current_settings)
                                        
                                        # Save to company profiles
                                        company_profiles = load_company_profiles()
                                        company_profiles[edit_company] = updated_profile
                                        save_company_profiles(company_profiles)
                                        
                                        # Update session state
                                        st.session_state.selected_company_profile = updated_profile
                                        st.session_state.editing_profile = updated_profile
                                        
                                        st.success(f"✅ Successfully saved changes to {edit_company}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to save changes: {str(e)}")
                else:
                    st.info("No saved companies yet. Create some posts and save company profiles!")
        else:
            st.info("💡 **No saved companies yet**\n\nAfter generating captions, you'll see an option to save the company profile for future use.")
        
        st.markdown("---")
        
        # Quick Start Guide
        st.markdown("### 🎯 Quick Start Guide")
        
        with st.expander("📋 How to Use", expanded=False):
            st.markdown("""
            **Step 1:** Choose your content source:
            • Upload image files (PNG, JPG, JPEG, WebP)
            • Use website images from analysis
            • Text-only mode for no-image posts
            
            **Step 2:** Enter business details:
            • Business type or company name
            • Website URL (optional, for enhanced context)
            • Quick category selection available
            
            **Step 3:** Customize style & settings:
            • Caption style (Professional, Casual, Inspirational, etc.)
            • Length (Short, Medium, Long)
            • Premium vs Standard AI model
            • Platform optimization and character limits
            
            **Step 4:** Generate & manage captions:
            • Generate 3 unique captions with one click
            • Mark captions as used (with toggle)
            • Download captions or save as company profile
            • Duplicate detection system alerts you to similar content
            
            **Step 5:** Advanced features (optional):
            • Save company profiles for instant reuse
            • Search and manage caption history from sidebar
            • Export usage data and analytics
            • Use focus keywords and target audience settings
            """)
        
        with st.expander("💡 Pro Tips"):
            st.markdown("""
            **Efficiency Tips:**
            • **Save company profiles** for instant setup on future posts
            • **Use website analysis** for enhanced brand context
            • **Load saved profiles** to auto-fill all information
            • **Batch processing** for multiple images at once
            • **Text-only mode** for quotes and announcements
            
            **Quality Tips:**
            • **Premium model (GPT-4o)** for highest quality results
            • **Website URLs** provide better brand-specific captions
            • **Clear business descriptions** improve caption relevance
            • **Mark captions as used** to avoid duplicates
            
            **Organization Tips:**
            • **Save generated captions** to review and reuse later
            • **Search & filter** used captions by business or date
            • **Export data** to CSV for external analysis
            • **Bulk delete** unwanted caption records
            """)
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            • **Website access blocked?** Try entering just business name/type
            • **Image upload fails?** Check file size (resize if needed)
            • **Slow generation?** Switch to Standard model (GPT-4o-mini)
            • **Clipboard not working?** Use file upload instead
            • **Duplicate captions?** Check the duplicate warnings when generating
            
            **Performance Issues:**
            • **App running slowly?** Use "Start Over" to clear session data
            • **Too many saved companies?** Delete unused profiles in sidebar
            • **Large caption history?** Clear used captions periodically
            
            **Feature Issues:**
            • **Page not responding?** Refresh the browser page
            • **Profile not loading?** Try re-selecting from dropdown
            • **Generation stuck?** Check your internet connection
            """)
        
        with st.expander("🆘 Need Help?"):
            col_help1, col_help2 = st.columns(2)
            with col_help1:
                if st.button("📖 View Full Documentation", type="primary", use_container_width=True):
                    st.session_state.show_documentation = True
                    st.rerun()
            with col_help2:
                if st.button("🐛 Report Issue/Feedback", type="secondary", use_container_width=True):
                    st.session_state.show_feedback = True
                    st.rerun()
        
        # Model usage indicator
        st.markdown("---")
        st.markdown("### 📊 Current Session")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Captions Generated", st.session_state.captions_generated)
        with col2:
            st.metric("Companies Saved", len(company_profiles))
        
        # Caption usage statistics
        st.markdown("### 📝 Caption Usage Stats")
        usage_stats = get_caption_usage_stats()
        
        usage_col1, usage_col2 = st.columns(2)
        with usage_col1:
            st.metric("Total Used", usage_stats['total_used'])
        with usage_col2:
            st.metric("This Week", usage_stats['recent_used'])
        
        if usage_stats['most_used_business'] != 'N/A':
            st.caption(f"🏆 Most Active: {usage_stats['most_used_business']}")
        
        # Show option to manage used captions
        if usage_stats['total_used'] > 0:
            with st.expander("🗑️ Manage Used Captions"):
                st.info(f"You have {usage_stats['total_used']} captions marked as used")
                
                # Add a search section for captions
                st.markdown("**Search Used Captions:**")
                search_query = st.text_input("Search captions:", placeholder="Enter keywords...")
                
                if search_query:
                    results = search_used_captions(search_query)
                    if results:
                        st.write(f"Found {len(results)} matching captions:")
                        for result in results[:5]:  # Show top 5 results
                            st.text(f"• {result['text'][:100]}..." if len(result['text']) > 100 else f"• {result['text']}")
                    else:
                        st.write("No matching captions found.")
                
                st.markdown("**Bulk Actions:**")
                if st.button("🔄 Clear All Used Captions", type="secondary"):
                    if os.path.exists(USED_CAPTIONS_FILE):
                        os.remove(USED_CAPTIONS_FILE)
                        st.success("✅ Cleared all used caption records")
                        st.rerun()
                
                # Export option
                if st.button("📥 Export Caption History", type="secondary"):
                    csv_data = export_caption_history()
                    if csv_data:
                        st.download_button(
                            "💾 Download CSV",
                            data=csv_data,
                            file_name=f"caption_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
                        st.rerun()
                st.caption("⚠️ This will reset duplicate detection")
        
        # Admin: Feedback Management
        st.markdown("### 💬 Feedback Management")
        feedback_summary = get_feedback_summary()
        
        if feedback_summary['total'] > 0:
            col_feedback1, col_feedback2 = st.columns(2)
            with col_feedback1:
                st.metric("Total Feedback", feedback_summary['total'])
            with col_feedback2:
                st.metric("This Week", feedback_summary['recent'])
            
            # Show feedback breakdown
            with st.expander(f"📊 View Feedback ({feedback_summary['total']} submissions)"):
                st.write("**Feedback Types:**")
                st.write(f"🐛 Bug Reports: {feedback_summary['bug_reports']}")
                st.write(f"💡 Feature Requests: {feedback_summary['feature_requests']}")
                st.write(f"❓ Questions/Support: {feedback_summary['questions']}")
                st.write(f"👍 General Feedback: {feedback_summary['general_feedback']}")
                
                # Load and display recent feedback
                feedback_list = load_feedback_submissions()
                if feedback_list:
                    st.markdown("**Recent Submissions:**")
                    
                    # Sort by date (most recent first)
                    sorted_feedback = sorted(feedback_list, 
                                           key=lambda x: x.get('submission_date', ''), 
                                           reverse=True)
                    
                    for i, feedback in enumerate(sorted_feedback[:5]):  # Show last 5
                        with st.container():
                            feedback_type = feedback.get('type', 'Unknown')
                            submission_date = feedback.get('submission_date', '')
                            
                            # Format date
                            try:
                                date_obj = datetime.fromisoformat(submission_date)
                                formatted_date = date_obj.strftime("%m/%d/%Y %H:%M")
                            except:
                                formatted_date = submission_date
                            
                            st.markdown(f"**#{feedback.get('id', i+1)} - {feedback_type}** *({formatted_date})*")
                            
                            # Show content based on type
                            if 'description' in feedback:
                                st.write(f"📝 {feedback['description'][:100]}..." if len(feedback.get('description', '')) > 100 else feedback.get('description', ''))
                            elif 'feedback' in feedback:
                                st.write(f"📝 {feedback['feedback'][:100]}..." if len(feedback.get('feedback', '')) > 100 else feedback.get('feedback', ''))
                            elif 'question' in feedback:
                                st.write(f"❓ {feedback['question'][:100]}..." if len(feedback.get('question', '')) > 100 else feedback.get('question', ''))
                            
                            if feedback.get('name') or feedback.get('email'):
                                contact_info = []
                                if feedback.get('name'):
                                    contact_info.append(feedback['name'])
                                if feedback.get('email'):
                                    contact_info.append(feedback['email'])
                                st.caption(f"👤 {' - '.join(contact_info)}")
                            
                            st.markdown("---")
                    
                    if len(feedback_list) > 5:
                        st.caption(f"... and {len(feedback_list) - 5} more submissions")
                
                # Export functionality
                st.markdown("**Management Actions:**")
                col_export, col_clear = st.columns(2)
                
                with col_export:
                    if st.button("📄 Export Feedback", help="Download all feedback as CSV"):
                        csv_data = export_feedback_data()
                        if csv_data:
                            st.download_button(
                                label="⬇️ Download CSV",
                                data=csv_data,
                                file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                
                with col_clear:
                    if st.button("🗑️ Clear All Feedback", help="Delete all feedback submissions", type="secondary"):
                        if os.path.exists(FEEDBACK_FILE):
                            os.remove(FEEDBACK_FILE)
                            st.success("✅ Cleared all feedback records")
                            st.rerun()
        else:
            st.info("No feedback submissions yet.")
        
        # Quick business templates
        st.markdown("### 🏢 Business Templates")
        templates = create_business_profile_template()
        selected_template = st.selectbox(
            "Quick Setup",
            ["Select Template..."] + list(templates.keys()),
            help="Pre-configured settings for common business types"
        )
        
        if selected_template != "Select Template...":
            return templates[selected_template]
        return None

def handle_single_page_layout(template_config):
    """Handle the single page layout with all inputs and outputs on one page."""
    
    # ========================================
    # SECTION 1: IMAGE & BUSINESS INFORMATION
    # ========================================
    st.header("📸 Image & Business Information")
    
    # Get current values from session state
    current_image = st.session_state.get('current_image')
    business_input = ""
    website_url = ""
    text_only_mode = False
    
    # Create main layout columns
    image_col, business_col = st.columns([1.5, 1])
    
    with image_col:
        # Content mode selection
        st.subheader("📷 Content Mode")
        text_only_mode = st.radio(
            "Choose content type:",
            ["Image + Text", "Text Only"],
            index=1 if st.session_state.get('temp_text_only_mode', False) else 0,
            help="Choose whether to include an image or create text-only posts",
            horizontal=True
        ) == "Text Only"
        
        if not text_only_mode:
            # Image source selection
            image_source = st.radio(
                "Image source:",
                ["Upload File", "From Website", "Clipboard"],
                help="Choose how to provide your image",
                horizontal=True
            )
            
            # Handle image upload/selection
            if image_source == "Upload File":
                uploaded_file = st.file_uploader(
                    "Choose an image file",
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    help="Upload an image file for caption generation"
                )
                if uploaded_file:
                    original_image = Image.open(uploaded_file)
                    st.session_state.original_image = original_image
                    
                    # If no current edited image exists, set it to the original
                    if 'current_image' not in st.session_state:
                        st.session_state.current_image = original_image.copy()
                    
                    current_image = st.session_state.current_image
                    st.success("✅ Image uploaded successfully!")
                    
                    # Image editing controls
                    st.markdown("#### 🎨 Image Editing")
                    
                    # Get original dimensions
                    orig_width, orig_height = original_image.size
                    
                    # Image size info
                    st.caption(f"📏 Original size: {orig_width}×{orig_height} pixels")
                    
                    # Create tabs for different editing options
                    edit_tab1, edit_tab2, edit_tab3 = st.tabs(["🔧 Resize", "✂️ Crop", "📥 Download"])
                    
                    with edit_tab1:
                        st.subheader("Resize Image")
                        
                        # Resize method selection
                        resize_method = st.radio(
                            "Resize method:",
                            ["Percentage", "Fixed Dimensions", "Social Media Presets"],
                            horizontal=True
                        )
                        
                        if resize_method == "Percentage":
                            resize_percent = st.slider(
                                "Resize percentage:",
                                min_value=10,
                                max_value=200,
                                value=100,
                                step=5,
                                help="100% = original size"
                            )
                            
                            new_width = int(orig_width * resize_percent / 100)
                            new_height = int(orig_height * resize_percent / 100)
                            
                        elif resize_method == "Fixed Dimensions":
                            col_w, col_h = st.columns(2)
                            with col_w:
                                new_width = st.number_input(
                                    "Width (pixels):",
                                    min_value=50,
                                    max_value=5000,
                                    value=orig_width,
                                    step=10
                                )
                            with col_h:
                                new_height = st.number_input(
                                    "Height (pixels):",
                                    min_value=50,
                                    max_value=5000,
                                    value=orig_height,
                                    step=10
                                )
                            
                            maintain_ratio = st.checkbox(
                                "Maintain aspect ratio",
                                value=True,
                                help="Keep original proportions"
                            )
                            
                            if maintain_ratio:
                                # Calculate based on width change
                                ratio = new_width / orig_width
                                new_height = int(orig_height * ratio)
                                st.caption(f"Adjusted height: {new_height}px (maintaining ratio)")
                        
                        else:  # Social Media Presets
                            preset_options = {
                                "Instagram Square (1080×1080)": (1080, 1080),
                                "Instagram Portrait (1080×1350)": (1080, 1350),
                                "Instagram Story (1080×1920)": (1080, 1920),
                                "Facebook Post (1200×630)": (1200, 630),
                                "Facebook Cover (1640×859)": (1640, 859),
                                "LinkedIn Post (1200×627)": (1200, 627),
                                "Twitter Post (1024×512)": (1024, 512),
                                "YouTube Thumbnail (1280×720)": (1280, 720)
                            }
                            
                            selected_preset = st.selectbox(
                                "Choose preset:",
                                list(preset_options.keys())
                            )
                            
                            new_width, new_height = preset_options[selected_preset]
                        
                        # Show new dimensions and apply button
                        st.info(f"New size will be: {new_width}×{new_height} pixels")
                        
                        if st.button("🔧 Apply Resize", type="primary"):
                            try:
                                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                st.session_state.current_image = resized_image
                                current_image = resized_image
                                st.success(f"✅ Image resized to {new_width}×{new_height}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error resizing image: {str(e)}")
                    
                    with edit_tab2:
                        st.subheader("Crop Image")
                        
                        current_width, current_height = current_image.size
                        
                        # Crop parameters
                        col1, col2 = st.columns(2)
                        with col1:
                            crop_left = st.number_input(
                                "Left margin (px):",
                                min_value=0,
                                max_value=current_width-50,
                                value=0,
                                step=10
                            )
                            crop_top = st.number_input(
                                "Top margin (px):",
                                min_value=0,
                                max_value=current_height-50,
                                value=0,
                                step=10
                            )
                        
                        with col2:
                            crop_right = st.number_input(
                                "Right margin (px):",
                                min_value=crop_left+50,
                                max_value=current_width,
                                value=current_width,
                                step=10
                            )
                            crop_bottom = st.number_input(
                                "Bottom margin (px):",
                                min_value=crop_top+50,
                                max_value=current_height,
                                value=current_height,
                                step=10
                            )
                        
                        # Quick crop presets
                        st.markdown("**Quick Crop Presets:**")
                        preset_col1, preset_col2, preset_col3 = st.columns(3)
                        
                        with preset_col1:
                            if st.button("Square Center"):
                                # Crop to square from center
                                size = min(current_width, current_height)
                                crop_left = (current_width - size) // 2
                                crop_top = (current_height - size) // 2
                                crop_right = crop_left + size
                                crop_bottom = crop_top + size
                        
                        with preset_col2:
                            if st.button("Remove 10% Border"):
                                # Remove 10% from each side
                                margin_x = int(current_width * 0.1)
                                margin_y = int(current_height * 0.1)
                                crop_left = margin_x
                                crop_top = margin_y
                                crop_right = current_width - margin_x
                                crop_bottom = current_height - margin_y
                        
                        with preset_col3:
                            if st.button("Reset to Full"):
                                crop_left = 0
                                crop_top = 0
                                crop_right = current_width
                                crop_bottom = current_height
                        
                        # Show crop dimensions
                        crop_width = crop_right - crop_left
                        crop_height = crop_bottom - crop_top
                        st.info(f"Cropped size will be: {crop_width}×{crop_height} pixels")
                        
                        if st.button("✂️ Apply Crop", type="primary"):
                            try:
                                cropped_image = current_image.crop((crop_left, crop_top, crop_right, crop_bottom))
                                st.session_state.current_image = cropped_image
                                current_image = cropped_image
                                st.success(f"✅ Image cropped to {crop_width}×{crop_height}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error cropping image: {str(e)}")
                    
                    with edit_tab3:
                        st.subheader("Download Options")
                        
                        # Format selection
                        download_format = st.selectbox(
                            "Download format:",
                            ["PNG (Best Quality)", "JPEG (Smaller Size)", "WebP (Modern)"]
                        )
                        
                        # Quality setting for JPEG
                        if "JPEG" in download_format:
                            jpeg_quality = st.slider(
                                "JPEG Quality:",
                                min_value=50,
                                max_value=100,
                                value=90,
                                help="Higher = better quality, larger file"
                            )
                        
                        # File name
                        default_name = f"edited_image_{datetime.now().strftime('%Y%m%d_%H%M')}"
                        filename = st.text_input(
                            "File name (without extension):",
                            value=default_name
                        )
                        
                        # Prepare download
                        format_map = {
                            "PNG (Best Quality)": ("PNG", "png"),
                            "JPEG (Smaller Size)": ("JPEG", "jpg"),
                            "WebP (Modern)": ("WebP", "webp")
                        }
                        
                        format_key, extension = format_map[download_format]
                        
                        # Create download buffer
                        img_buffer = io.BytesIO()
                        
                        if format_key == "JPEG":
                            # Convert to RGB if necessary for JPEG
                            if current_image.mode in ('RGBA', 'LA', 'P'):
                                # Create white background
                                rgb_image = Image.new('RGB', current_image.size, (255, 255, 255))
                                if current_image.mode == 'P':
                                    current_image = current_image.convert('RGBA')
                                rgb_image.paste(current_image, mask=current_image.split()[-1] if current_image.mode == 'RGBA' else None)
                                current_image.save(img_buffer, format=format_key, quality=jpeg_quality)
                            else:
                                current_image.save(img_buffer, format=format_key, quality=jpeg_quality)
                        else:
                            current_image.save(img_buffer, format=format_key)
                        
                        img_buffer.seek(0)
                        
                        # Show file info
                        file_size = len(img_buffer.getvalue()) / 1024  # KB
                        current_size = current_image.size
                        st.info(f"📄 File size: {file_size:.1f} KB | Dimensions: {current_size[0]}×{current_size[1]} pixels")
                        
                        # Download button
                        st.download_button(
                            label=f"📥 Download as {format_key}",
                            data=img_buffer.getvalue(),
                            file_name=f"{filename}.{extension}",
                            mime=f"image/{extension}",
                            type="primary",
                            use_container_width=True
                        )
                        
                        # Reset to original button
                        if st.button("🔄 Reset to Original", type="secondary", use_container_width=True):
                            st.session_state.current_image = st.session_state.original_image.copy()
                            st.success("✅ Reset to original image")
                            st.rerun()
            
            elif image_source == "From Website":
                if st.session_state.get('website_analysis'):
                    website_images = st.session_state.website_analysis.get('images', [])
                    if website_images:
                        selected_img_idx = st.selectbox(
                            "Select website image:",
                            range(len(website_images)),
                            format_func=lambda x: f"Image {x+1}: {website_images[x]['description'][:50]}..."
                        )
                        
                        if st.button("🖼️ Use Selected Image"):
                            try:
                                img_url = website_images[selected_img_idx]['url']
                                response = requests.get(img_url, timeout=10)
                                website_image = Image.open(io.BytesIO(response.content))
                                
                                # Store both original and current versions
                                st.session_state.original_image = website_image.copy()
                                st.session_state.current_image = website_image.copy()
                                current_image = website_image
                                
                                st.success("✅ Website image loaded!")
                            except Exception as e:
                                st.error(f"Failed to load image: {str(e)}")
                    else:
                        st.info("No website images found. Analyze a website first.")
                else:
                    st.info("No website analysis available. Add a website URL and analyze it first.")
            
            elif image_source == "Clipboard":
                st.info("💡 Clipboard feature not available. Please use file upload instead.")
            
            # Display current image
            if current_image:
                st.markdown("#### 🖼️ Current Image Preview")
                
                # Display image in a more compact way
                img_col, info_col = st.columns([2, 1])
                
                with img_col:
                    # Display with limited width for better layout
                    st.image(current_image, caption="Current Image", width=300)
                
                with info_col:
                    # Show image information
                    width, height = current_image.size
                    st.metric("Width", f"{width}px")
                    st.metric("Height", f"{height}px")
                    
                    # File size estimation
                    img_buffer = io.BytesIO()
                    current_image.save(img_buffer, format='PNG')
                    file_size = len(img_buffer.getvalue()) / 1024  # KB
                    st.metric("Est. Size", f"{file_size:.1f} KB")
                    
                    # Quick actions
                    if st.button("🗑️ Clear Image", use_container_width=True):
                        # Clear both current and original images
                        if 'current_image' in st.session_state:
                            del st.session_state.current_image
                        if 'original_image' in st.session_state:
                            del st.session_state.original_image
                        st.rerun()
                    
                    # Show if image has been edited
                    if ('original_image' in st.session_state and 
                        st.session_state.original_image.size != current_image.size):
                        st.caption("✂️ Image has been edited")
                    elif 'original_image' in st.session_state:
                        st.caption("📷 Original image")
        else:
            st.info("📝 **Text-Only Mode:** Captions will be generated without image references.")
    
    with business_col:
        # Business information
        st.subheader("🏢 Business Information")
        
        # Pre-fill from loaded profile or template
        default_business = ""
        default_website = ""
        auto_filled_business = ""
        
        if st.session_state.get('selected_company_profile'):
            profile = st.session_state.selected_company_profile
            default_business = profile.get('business_input', '')
            default_website = profile.get('website_url', '')
        elif template_config:
            default_business = f"{template_config.get('type', 'business')} focusing on {', '.join(template_config.get('keywords', [])[:3])}"
        
        # Check if we have auto-filled business name from website
        if st.session_state.get('auto_filled_business_name'):
            auto_filled_business = st.session_state.auto_filled_business_name
            # Use auto-filled name if no manual business input exists
            if not default_business or default_business == st.session_state.get('previous_auto_fill', ''):
                default_business = auto_filled_business
        
        website_url = st.text_input(
            "🔗 Website URL (Optional)",
            value=default_website,
            placeholder="https://yourcompany.com",
            help="Provide website URL for enhanced context and auto-fill business name",
            key="website_url_input"
        )
        
        # Auto-analyze website when URL changes
        current_url = website_url.strip() if website_url else ""
        previous_url = st.session_state.get('previous_website_url', '')
        
        # Normalize URL by adding https:// if missing
        if current_url and not current_url.startswith(('http://', 'https://')):
            current_url = 'https://' + current_url
        
        if current_url and current_url != previous_url and len(current_url) > 10:  # Basic URL validation
            st.session_state.previous_website_url = current_url
            
            with st.spinner("🌐 Auto-analyzing website for business name..."):
                website_info = analyze_website_with_spinner(current_url)
                if website_info:
                    st.session_state.website_analysis = website_info
                    
                    # Extract and clean business name from website title
                    raw_title = website_info.get('title', '')
                    if raw_title:
                        # Clean the title - remove common suffixes and split by common separators
                        clean_title = raw_title.split('|')[0].split('-')[0].split('–')[0].strip()
                        
                        # Remove common website suffixes
                        suffixes_to_remove = [
                            'Home', 'Welcome', 'Official Site', 'Official Website', 
                            'Homepage', 'Main Page', 'Index', '.com', '.net', '.org'
                        ]
                        
                        for suffix in suffixes_to_remove:
                            if clean_title.endswith(suffix):
                                clean_title = clean_title[:-len(suffix)].strip()
                        
                        # Store the auto-filled business name
                        st.session_state.auto_filled_business_name = clean_title
                        st.session_state.previous_auto_fill = clean_title
                        
                        # Show success message
                        st.success(f"✅ Website analyzed! Auto-filled business name: **{clean_title}**")
                        st.info("� You can edit the business name below if needed.")
                        st.rerun()
        
        business_input = st.text_area(
            "Business Type / Company Description",
            value=default_business,
            placeholder="e.g., Italian restaurant, fitness studio, consulting firm, online store, etc.",
            height=120,
            help="Describe your business type or provide company details (auto-filled from website if available)"
        )
        
        # Manual website analysis button (for re-analysis or troubleshooting)
        if website_url and website_url.strip():
            if st.button("� Re-analyze Website", type="secondary", help="Re-analyze website or force analysis"):
                with st.spinner("🌐 Re-analyzing website..."):
                    website_info = analyze_website_with_spinner(website_url.strip())
                    if website_info:
                        st.session_state.website_analysis = website_info
                        st.success("✅ Website re-analyzed successfully!")
                        st.rerun()
        
        # Show website analysis status
        if st.session_state.get('website_analysis'):
            analysis = st.session_state.website_analysis
            st.success(f"✅ Website analyzed: {len(analysis.get('pages_analyzed', []))} pages")
    
    # Store values in session state
    st.session_state.temp_business_input = business_input
    st.session_state.temp_website_url = website_url
    st.session_state.temp_text_only_mode = text_only_mode
    
    st.markdown("---")
    
    # ========================================
    # SECTION 2: STYLE & CUSTOMIZATION
    # ========================================
    st.header("🎨 Style & Customization")
    
    style_col1, style_col2, style_col3 = st.columns(3)
    
    with style_col1:
        st.subheader("📝 Caption Style")
        
        # Pre-fill from loaded profile or template
        default_style = "Professional"
        default_length = 1  # Medium
        
        if st.session_state.get('selected_company_profile'):
            profile = st.session_state.selected_company_profile
            default_style = profile.get('caption_style', 'Professional')
            length_options = ["Short (3-4 sentences)", "Medium (4-6 sentences)", "Long (6+ sentences)"]
            try:
                default_length = length_options.index(profile.get('caption_length', 'Medium (4-6 sentences)'))
            except ValueError:
                default_length = 1
        elif template_config:
            default_style = template_config.get('tone', 'Professional')
        
        caption_style = st.selectbox(
            "Style:",
            ["Professional", "Casual & Friendly", "Inspirational", "Educational", "Promotional"],
            index=["Professional", "Casual & Friendly", "Inspirational", "Educational", "Promotional"].index(default_style),
            help="Choose the tone and style for your captions"
        )
        
        caption_length = st.selectbox(
            "Length:",
            ["Short (3-4 sentences)", "Medium (4-6 sentences)", "Long (6+ sentences)"],
            index=default_length,
            help="Preferred length for generated captions"
        )
    
    with style_col2:
        st.subheader("⚙️ AI Settings")
        
        # Pre-fill from loaded profile
        default_premium = False
        default_cta = True
        
        if st.session_state.get('selected_company_profile'):
            profile = st.session_state.selected_company_profile
            default_premium = profile.get('use_premium_model', False)
            default_cta = profile.get('include_cta', True)
        
        use_premium_model = st.checkbox(
            "⭐ Use Premium Model (GPT-4o)",
            value=default_premium,
            help="Higher quality results but costs more. Uncheck for cost-effective GPT-4o-mini."
        )
        
        include_cta = st.checkbox(
            "🎯 Include Call-to-Action",
            value=default_cta,
            help="Add subtle calls-to-action in captions"
        )
        
        # Character limit preference
        character_limit_preference = st.selectbox(
            "📱 Platform Optimization:",
            ["No limit", "Facebook (≤500 chars)", "Instagram (≤400 chars)", "LinkedIn (≤700 chars)", "Twitter/X (≤280 chars)", "All platforms (≤280 chars)"],
            help="Optimize captions to fit specific social media platform character limits"
        )
    
    with style_col3:
        st.subheader("🎯 Advanced Options")
        
        # Pre-fill advanced options from profile
        default_focus = ""
        default_avoid = ""
        default_audience = 0
        
        if st.session_state.get('selected_company_profile'):
            profile = st.session_state.selected_company_profile
            default_focus = profile.get('focus_keywords', '')
            default_avoid = profile.get('avoid_words', '')
            audience_options = ["General", "Young Adults (18-35)", "Professionals", "Families", "Seniors", "Local Community"]
            try:
                default_audience = audience_options.index(profile.get('target_audience', 'General'))
            except ValueError:
                default_audience = 0
        
        focus_keywords = st.text_input(
            "Focus Keywords:",
            value=default_focus,
            placeholder="e.g., organic, handmade, premium",
            help="Keywords to emphasize in captions"
        )
        
        avoid_words = st.text_input(
            "Words to Avoid:",
            value=default_avoid,
            placeholder="e.g., cheap, basic, generic",
            help="Words to avoid in captions"
        )
        
        target_audience = st.selectbox(
            "Target Audience:",
            ["General", "Young Adults (18-35)", "Professionals", "Families", "Seniors", "Local Community"],
            index=default_audience,
            help="Tailor captions to specific audience"
        )
    
    # Store style settings in session state
    st.session_state.temp_caption_style = caption_style
    st.session_state.temp_caption_length = caption_length
    st.session_state.temp_use_premium_model = use_premium_model
    st.session_state.temp_include_cta = include_cta
    st.session_state.temp_focus_keywords = focus_keywords
    st.session_state.temp_avoid_words = avoid_words
    st.session_state.temp_target_audience = target_audience
    st.session_state.temp_character_limit_preference = character_limit_preference
    
    st.markdown("---")
    
    # ========================================
    # SECTION 3: GENERATION & RESULTS
    # ========================================
    st.header("🚀 Generate Captions")
    
    # Check if ready to generate
    generation_ready = ((current_image is not None or text_only_mode) and 
                        business_input and business_input.strip())
    
    if not generation_ready:
        st.warning("⚠️ Please complete the following to generate captions:")
        if not current_image and not text_only_mode:
            st.write("• 📸 Upload an image or choose text-only mode")
        if not business_input or not business_input.strip():
            st.write("• 🏢 Enter business information")
    else:
        # Show current configuration
        with st.expander("📋 Current Configuration", expanded=False):
            config_col1, config_col2 = st.columns(2)
            with config_col1:
                st.write(f"**Business:** {business_input[:50]}{'...' if len(business_input) > 50 else ''}")
                st.write(f"**Style:** {caption_style}")
                st.write(f"**Length:** {caption_length}")
                st.write(f"**Mode:** {'Text-Only' if text_only_mode else 'Image-Based'}")
            with config_col2:
                st.write(f"**Model:** {'GPT-4o (Premium)' if use_premium_model else 'GPT-4o-mini'}")
                st.write(f"**CTA:** {'Yes' if include_cta else 'No'}")
                st.write(f"**Website:** {'Analyzed' if st.session_state.get('website_analysis') else 'Not used'}")
                st.write(f"**Platform:** {character_limit_preference}")
        
        # Generate button
        generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
        with generate_col2:
            generate_button_text = "🚀 Generate Text-Only Captions" if text_only_mode else "🚀 Generate Image Captions"
            
            if st.button(generate_button_text, type="primary", use_container_width=True):
                # Prepare enhanced business input
                enhanced_business_input = business_input
                if focus_keywords:
                    enhanced_business_input += f" (focus on: {focus_keywords})"
                if target_audience != "General":
                    enhanced_business_input += f" (targeting: {target_audience})"
                
                # Generate captions
                with st.spinner(f"🤖 Generating {'text-only ' if text_only_mode else ''}captions..."):
                    result = generate_captions(
                        current_image if not text_only_mode else None,
                        enhanced_business_input,
                        website_url,
                        use_premium_model,
                        caption_style,
                        include_cta,
                        caption_length,
                        text_only_mode,
                        character_limit_preference
                    )
                    
                    if result:
                        st.session_state.generated_captions = result
                        
                        # Update persistent captions counter
                        new_total = increment_captions_generated(3)
                        st.session_state.captions_generated = new_total
                        
                        # Store current settings for potential saving
                        st.session_state.current_settings = {
                            'business_input': business_input,
                            'website_url': website_url,
                            'caption_style': caption_style,
                            'caption_length': caption_length,
                            'use_premium_model': use_premium_model,
                            'include_cta': include_cta,
                            'focus_keywords': focus_keywords,
                            'avoid_words': avoid_words,
                            'target_audience': target_audience,
                            'text_only_mode': text_only_mode,
                            'character_limit_preference': character_limit_preference
                        }
                        
                        st.success("✅ Captions generated successfully!")
                        st.rerun()
    
    # ========================================
    # SECTION 4: GENERATED CAPTIONS DISPLAY
    # ========================================
    if st.session_state.get('generated_captions'):
        st.markdown("---")
        st.header("📝 Your Generated Captions")
        
        captions = st.session_state.generated_captions.split('\n\n')
        
        for i, caption in enumerate(captions):
            if caption.strip():
                with st.container():
                    # Check if caption was previously used
                    is_duplicate, duplicate_info = is_caption_duplicate(caption.strip())
                    
                    # Caption header
                    if is_duplicate:
                        st.subheader(f"⚠️ Caption {i+1} (Previously Used)")
                        st.warning(f"🔄 Similar caption used on {duplicate_info['used_date'][:10]} for {duplicate_info.get('business', 'Unknown')}")
                    else:
                        st.subheader(f"✨ Caption {i+1} (New)")
                    
                    # Caption content
                    caption_col, action_col = st.columns([4, 1])
                    
                    with caption_col:
                        st.text_area(
                            "Caption Text:",
                            value=caption.strip(),
                            height=120,
                            key=f"caption_display_{i}",
                            help="Caption text - copy this to use in your social media posts"
                        )
                        
                        # Character count and platform suitability
                        char_count = len(caption.strip())
                        
                        platform_col1, platform_col2, platform_col3, platform_col4 = st.columns(4)
                        with platform_col1:
                            fb_suitable = "✅" if char_count <= 500 else "⚠️"
                            st.caption(f"Facebook: {fb_suitable} ({char_count}/500)")
                        with platform_col2:
                            ig_suitable = "✅" if char_count <= 400 else "⚠️"
                            st.caption(f"Instagram: {ig_suitable} ({char_count}/400)")
                        with platform_col3:
                            li_suitable = "✅" if char_count <= 700 else "⚠️"
                            st.caption(f"LinkedIn: {li_suitable} ({char_count}/700)")
                        with platform_col4:
                            tw_suitable = "✅" if char_count <= 280 else "⚠️"
                            st.caption(f"Twitter/X: {tw_suitable} ({char_count}/280)")
                    
                    with action_col:
                        # Mark as used toggle
                        is_currently_used = is_caption_duplicate(caption.strip())[0]
                        
                        if is_currently_used:
                            if st.button(f"🔄 Unmark", key=f"unmark_{i}", help="Remove from usage history"):
                                if unmark_caption_as_used(caption.strip()):
                                    st.success("✅ Removed from history!")
                                    st.rerun()
                        else:
                            if st.button(f"✅ Mark Used", key=f"mark_{i}", help="Mark as used"):
                                mark_caption_as_used(caption.strip(), business_input)
                                st.success("📝 Marked as used!")
                                st.rerun()
                
                st.markdown("---")
        
        # ========================================
        # SECTION 5: DOWNLOAD & SAVE OPTIONS
        # ========================================
        st.header("💾 Download & Save Options")
        
        download_col1, download_col2, download_col3, save_col = st.columns(4)
        
        with download_col1:
            st.download_button(
                label="📄 Download Captions",
                data=st.session_state.generated_captions,
                file_name=f"captions_{business_input.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with download_col2:
            if current_image and not text_only_mode:
                img_buffer = io.BytesIO()
                current_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                st.download_button(
                    label="🖼️ Download Image",
                    data=img_buffer.getvalue(),
                    file_name=f"image_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.info("No image to download")
        
        with download_col3:
            # Create combined package
            combined_content = f"Social Media Captions for {business_input}\n"
            combined_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            combined_content += f"Style: {caption_style} | Length: {caption_length}\n"
            combined_content += f"Mode: {'Text-Only' if text_only_mode else 'Image-Based'}\n\n"
            combined_content += "=" * 50 + "\n\n"
            combined_content += st.session_state.generated_captions
            
            st.download_button(
                label="📦 Download Package",
                data=combined_content,
                file_name=f"package_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with save_col:
            # Company profile save option
            if st.button("💾 Save Company", use_container_width=True):
                if st.session_state.get('current_settings'):
                    settings = st.session_state.current_settings
                    profile_data = create_profile_data_from_settings(settings)
                    company_name = settings.get('business_input', 'Unknown Company')
                    
                    if save_company_profile(company_name, profile_data):
                        st.success(f"✅ Saved: {company_name}")
                    else:
                        st.error("❌ Failed to save")
                else:
                    st.warning("⚠️ No settings to save")

# === Main Application Functions ===
def initialize_session_state():
    """Initialize session state variables."""
    # Load persistent captions counter
    stats = load_app_statistics()
    
    default_values = {
        'generated_captions': None,
        'current_image': None,
        'website_analysis': None,
        'captions_generated': stats['total_captions_generated'],
        'show_documentation': False,
        'show_feedback': False
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def display_page_header():
    """Display the main page header with metrics."""
    col_title, col_metrics, col_help = st.columns([2.5, 1, 0.5])
    
    with col_title:
        st.title("🚀 Adcellerant Social Caption Generator")
        st.markdown("**AI-Powered Social Media Caption Generator with Advanced Website Analysis**")
    
    with col_metrics:
        st.metric("🎯 Captions Created", st.session_state.captions_generated)
    
    with col_help:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        if st.button("📖", help="View Documentation & Help", type="secondary"):
            st.session_state.show_documentation = True
            st.rerun()
        if st.button("💬", help="Report Issue or Suggest Improvement", type="secondary"):
            st.session_state.show_feedback = True
            st.rerun()

def show_documentation_popup():
    """Display comprehensive documentation in a popup."""
    if st.session_state.get('show_documentation'):
        st.markdown("---")
        
        # Header with close button using reusable component
        create_header_with_close_button("📖 Complete Feature Documentation", "show_documentation")
        
        # Create tabs for different documentation sections
        doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
            "🚀 Getting Started", "🎨 Features Guide", "⚙️ Advanced Usage", "❓ FAQ"
        ])
        
        with doc_tab1:
            st.markdown("""
            ### 🎯 Welcome to Adcellerant Social Caption Generator!
            
            This AI-powered tool helps you create engaging social media captions for your business posts.
            
            #### **Quick Setup (2 minutes):**
            1. **Choose your content type** (Image upload, clipboard, or text-only)
            2. **Enter business information** (Name, type, website)
            3. **Select caption style** (Professional, Casual, Inspirational, etc.)
            4. **Generate captions** with one click
            5. **Copy and use** your favorite caption
            
            #### **Key Benefits:**
            - 🤖 **AI-Powered**: Uses GPT-4 for high-quality, engaging captions
            - 🌐 **Website Analysis**: Analyzes your website for brand-specific context
            - 📱 **Multi-Platform**: Works for Instagram, Facebook, LinkedIn, Twitter
            - 🔄 **Duplicate Prevention**: Tracks used captions to avoid repetition
            - 💾 **Company Profiles**: Save settings for instant future use
            - 📊 **Usage Analytics**: Track and export your caption history
            """)
        
        with doc_tab2:
            st.markdown("""
            ### 🎨 Complete Features Guide
            
            #### **Section 1: 📸 Image & Business Information**
            - **Content Modes**: Image + Text or Text-Only posting options
            - **Image Sources**: Upload files, use website images, or clipboard
            - **Business Input**: Company name, business type, website URL
            - **Website Analysis**: Automatic analysis for brand context
            - **Quick Templates**: Pre-configured business type templates
            
            #### **Section 2: 🎨 Style & Customization**
            - **Caption Styles**: Professional, Casual & Friendly, Inspirational, Educational, Promotional
            - **Length Options**: Short (3-4 sentences), Medium (4-6), Long (6+)
            - **AI Models**: Premium (GPT-4o) vs Standard (GPT-4o-mini)
            - **Platform Optimization**: Character limits for specific social platforms
            - **Advanced Options**: Focus keywords, target audience, words to avoid
            
            #### **Section 3: 🚀 Generation & Results**
            - **Smart Validation**: Checks that all required inputs are provided
            - **Configuration Preview**: Shows current settings before generation
            - **Real-time Generation**: AI-powered caption creation with progress indicators
            - **Multiple Attempts**: Automatic retry for better variety if duplicates detected
            
            #### **Section 4: � Generated Captions Display**
            - **3 Unique Captions**: Each generation creates 3 different options
            - **Usage Tracking**: Mark captions as used to avoid duplicates
            - **Platform Compatibility**: Shows character counts for different social platforms
            - **Duplicate Detection**: Warns if similar captions were used before
            
            #### **Section 5: � Download & Save Options**
            - **Multiple Formats**: Download captions, images, or combined packages
            - **Company Profiles**: Save current settings for future use
            - **Instant Access**: One-click downloading and saving
            - **Organization**: Structured file naming for easy management
            """)
        
        with doc_tab3:
            st.markdown("""
            ### ⚙️ Advanced Usage Tips
            
            #### **Single-Page Workflow:**
            - **Top-to-Bottom Flow**: Complete each section in order for best results
            - **Real-time Updates**: Changes are automatically saved as you work
            - **Section Navigation**: Use section headers to quickly jump between areas
            - **Live Preview**: See configuration summary before generating
            
            #### **Company Profile Management:**
            - **Save Profiles**: Store business info, style preferences, and settings
            - **Quick Load**: Auto-fill all fields with one click from sidebar
            - **Profile Templates**: Use pre-configured settings for common business types
            - **Batch Efficiency**: Save profiles for multiple clients or brands
            
            #### **Caption Optimization:**
            - **Website URLs**: Always include your website for better brand context
            - **Business Descriptions**: Be specific about your services/products
            - **Style Consistency**: Use the same style for brand voice consistency
            - **Platform Strategy**: Choose character limits based on your target platform
            
            #### **Duplicate Management:**
            - **Usage Tracking**: Mark captions as used to build history
            - **Smart Detection**: System warns about similar content automatically
            - **Search & Filter**: Find specific captions in your history
            - **Bulk Operations**: Manage multiple caption records at once
            - **Toggle Used Status**: Mark/unmark captions as used
            - **Similar Caption Warnings**: Get alerts for potential duplicates
            - **History Search**: Check if you've used similar content before
            - **Fresh Generation**: Use retry system for completely new captions
            
            #### **Workflow Optimization:**
            - **Text-Only Mode**: Perfect for quotes, announcements, behind-the-scenes
            - **Batch Processing**: Ideal for product launches, event photos
            - **Premium Model**: Use for important posts, client work, special campaigns
            - **Standard Model**: Use for regular posting, testing, high-volume needs
            
            #### **Data Management:**
            - **Export Options**: Download caption history, company profiles
            - **Clear Data**: Reset used captions, delete old companies
            - **Session Management**: Use "Start Over" to clear temporary data
            - **Backup Strategy**: Regularly export important company profiles
            """)
        
        with doc_tab4:
            st.markdown("""
            ### ❓ Frequently Asked Questions
            
            #### **Getting Started:**
            **Q: Do I need an account to use this?**
            A: You need the application password. Contact Maddie Stitt for access.
            
            **Q: What image formats are supported?**
            A: PNG, JPG, JPEG, and WebP files are supported.
            
            **Q: Can I use this without images?**
            A: Yes! Text-only mode creates captions based on business information only.
            
            #### **Features & Usage:**
            **Q: What's the difference between Premium and Standard models?**
            A: Premium (GPT-4o) provides higher quality, more creative captions but costs more. Standard (GPT-4o-mini) is faster and more cost-effective.
            
            **Q: How does duplicate detection work?**
            A: The system tracks captions you mark as "used" and warns if new captions are similar.
            
            **Q: Can I edit generated captions?**
            A: Copy captions to your preferred text editor to make modifications before posting.
            
            #### **Technical Issues:**
            **Q: Website analysis failed - what should I do?**
            A: Some websites block automated access. Enter your business type manually for good results.
            
            **Q: Clipboard paste isn't working?**
            A: Use the "Web Clipboard" alternative methods, or switch to file upload.
            
            **Q: The app is running slowly?**
            A: Click "Start Over" to clear session data, or try using the Standard model.
            
            #### **Data & Privacy:**
            **Q: Is my data saved permanently?**
            A: Yes! Company profiles and caption history are saved to the server and persist across browser sessions. All authorized users can access the shared data.
            
            **Q: Can I export my data?**
            A: Yes! Use the export features in Caption History tab and company management.
            
            **Q: How do I delete my data?**
            A: Use the clear functions in the sidebar to remove data from the shared database.
            """)
        
        st.markdown("---")

def show_feedback_popup():
    """Display feedback form for bug reports and feature requests."""
    if st.session_state.get('show_feedback'):
        st.markdown("---")
        
        # Header with close button using reusable component
        create_header_with_close_button("💬 User Feedback & Support", "show_feedback")
        
        st.markdown("""
        **Help us improve!** Your feedback is valuable for making this tool better.
        """)
        
        # Feedback type selection
        feedback_type = st.radio(
            "What type of feedback do you have?",
            ["🐛 Bug Report", "💡 Feature Request", "👍 General Feedback", "❓ Question/Support"],
            horizontal=True
        )
        
        col_form1, col_form2 = st.columns([2, 1])
        
        with col_form1:
            # Priority/Impact for bugs
            if feedback_type == "🐛 Bug Report":
                priority = st.selectbox(
                    "Bug Severity:",
                    ["🔴 Critical (App unusable)", "🟡 Medium (Feature broken)", "🟢 Low (Minor issue)"]
                )
                
                st.markdown("**Please describe the bug:**")
                bug_description = st.text_area(
                    "What happened? What did you expect to happen?",
                    placeholder="Example: When I click 'Generate Captions', I get an error message instead of captions...",
                    height=100
                )
                
                steps_to_reproduce = st.text_area(
                    "Steps to reproduce (optional):",
                    placeholder="1. Go to Image & Business tab\n2. Upload an image\n3. Click Generate...",
                    height=80
                )
                
                browser_info = st.text_input(
                    "Browser & System (optional):",
                    placeholder="Chrome on Windows 11, Safari on Mac, etc."
                )
            
            elif feedback_type == "💡 Feature Request":
                st.markdown("**Describe your feature idea:**")
                feature_description = st.text_area(
                    "What feature would you like to see?",
                    placeholder="Example: I'd like to be able to schedule posts directly from the app...",
                    height=100
                )
                
                use_case = st.text_area(
                    "How would this help you?",
                    placeholder="This would save me time because...",
                    height=80
                )
                
                priority = st.selectbox(
                    "How important is this to you?",
                    ["⭐ Nice to have", "⭐⭐ Would be helpful", "⭐⭐⭐ Really need this!"]
                )
            
            elif feedback_type == "👍 General Feedback":
                st.markdown("**Share your thoughts:**")
                general_feedback = st.text_area(
                    "What's working well? What could be improved?",
                    placeholder="I love the website analysis feature, but I wish...",
                    height=120
                )
                
                rating = st.select_slider(
                    "Overall experience:",
                    options=["😞 Poor", "😐 Okay", "🙂 Good", "😊 Great", "🤩 Excellent"],
                    value="🙂 Good"
                )
            
            else:  # Question/Support
                st.markdown("**What can we help with?**")
                question = st.text_area(
                    "Describe your question or issue:",
                    placeholder="I'm not sure how to...",
                    height=100
                )
                
                question_type = st.selectbox(
                    "Question category:",
                    ["How to use a feature", "Technical issue", "Account/Access", "General question"]
                )
        
        with col_form2:
            st.markdown("### 📧 Contact Information")
            st.info("""
            **For immediate support:**
            📧 Contact: Maddie Stitt
            
            **What happens next:**
            • Your feedback is recorded
            • High priority issues are addressed first
            • Feature requests are reviewed monthly
            • You may be contacted for clarification
            """)
            
            # Optional contact info
            st.markdown("**Optional: Leave contact info for follow-up**")
            contact_email = st.text_input("Email (optional):", placeholder="your@email.com")
            contact_name = st.text_input("Name (optional):", placeholder="Your name")
        
        # Submit button
        st.markdown("---")
        col_submit, col_cancel = st.columns([1, 4])
        
        with col_submit:
            if st.button("📤 Submit Feedback", type="primary"):
                # Prepare feedback data
                feedback_data = {
                    'type': feedback_type,
                    'email': contact_email,
                    'name': contact_name
                }
                
                # Add type-specific data
                if feedback_type == "🐛 Bug Report":
                    feedback_data.update({
                        'severity': priority,
                        'description': bug_description,
                        'steps': steps_to_reproduce,
                        'browser_info': browser_info
                    })
                elif feedback_type == "💡 Feature Request":
                    feedback_data.update({
                        'description': feature_description,
                        'use_case': use_case,
                        'priority': priority
                    })
                elif feedback_type == "👍 General Feedback":
                    feedback_data.update({
                        'feedback': general_feedback,
                        'rating': rating
                    })
                else:  # Question/Support
                    feedback_data.update({
                        'question': question,
                        'category': question_type
                    })
                
                # Save feedback
                if save_feedback_submission(feedback_data):
                    st.success("✅ Thank you! Your feedback has been recorded and saved.")
                    st.info("� Your feedback helps us improve the tool for everyone!")
                else:
                    st.error("❌ Sorry, there was an error saving your feedback. Please try again.")
                
                # Clear the form
                st.session_state.show_feedback = False
                st.rerun()
        
        st.markdown("---")

def create_main_tabs():
    """Create and return the main application tabs."""
    return st.tabs([
        "📸 Image & Business", 
        "🎨 Style Settings", 
        "🌐 Website Analysis", 
        "📱 Generated Captions", 
        "🔄 Batch Processing",
        "📝 Caption History"
    ])

def handle_image_business_tab():
    """Handle the Image & Business tab content."""
    st.header("📸 Image Selection & Business Information")
    
    # Check for loaded company profile
    _display_loaded_profile_info()
    
    # Create layout columns
    img_col, business_col = st.columns([1.2, 1])
    
    # Handle image selection
    with img_col:
        image, text_only_mode = _handle_image_selection()
    
    # Handle business information
    with business_col:
        business_input, website_url = _handle_business_information()
    
    # Store values in session state
    _store_tab_values({
        'business_input': business_input,
        'website_url': website_url,
        'text_only_mode': text_only_mode
    })
    
    return image, business_input, website_url, text_only_mode

def _display_loaded_profile_info():
    """Display information about loaded company profile."""
    if st.session_state.get('selected_company_profile'):
        profile = st.session_state.selected_company_profile
        company_name = st.session_state.get('selected_company_name', 'Unknown')
        
        if st.session_state.get('editing_company'):
            st.warning(f"✏️ **Editing Mode:** {st.session_state.editing_company}")
            st.info("💡 Update the information below and save when ready.")
            
            if st.button("🔄 Cancel Editing", type="secondary"):
                _clear_editing_mode()
                st.rerun()
        else:
            st.success(f"✅ **Loaded Profile:** {company_name}")
        
        with st.expander("📋 Loaded Company Details", expanded=True):
            _display_profile_details(profile)
        
        if not st.session_state.get('editing_company'):
            if st.button("🔄 Clear Loaded Profile", type="secondary"):
                _clear_loaded_profile()
                st.rerun()

def _display_profile_details(profile):
    """Display company profile details in columns."""
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Business:** {profile.get('business_input', 'N/A')}")
        st.write(f"**Website:** {profile.get('website_url', 'N/A')}")
        st.write(f"**Style:** {profile.get('caption_style', 'N/A')}")
    with col2:
        st.write(f"**Length:** {profile.get('caption_length', 'N/A')}")
        st.write(f"**Model:** {'Premium' if profile.get('use_premium_model') else 'Standard'}")
        st.write(f"**CTA:** {'Yes' if profile.get('include_cta') else 'No'}")

def _handle_image_selection():
    """Handle image selection UI and logic."""
    st.subheader("📷 Choose Your Image")
    
    # Show current image status and clear option
    if st.session_state.get('current_image'):
        col_status, col_clear = st.columns([3, 1])
        with col_status:
            image_source = "Unknown"
            if st.session_state.get('uploaded_image'):
                image_source = f"Uploaded file: {st.session_state.uploaded_image}"
            elif st.session_state.get('clipboard_image'):
                image_source = "Clipboard"
            elif st.session_state.get('selected_web_image') is not None:
                image_num = st.session_state.selected_web_image + 1
                image_source = f"Website Image {image_num}"
            
            st.success(f"✅ Current image: {image_source}")
        
        with col_clear:
            if st.button("🗑️ Clear", help="Clear current image", type="secondary"):
                _clear_image_session_state()
                st.rerun()
    
    # Build options list based on available functionality
    image_options = ["📁 Upload File", "🌐 Use Website Image", "📝 Text-Only (No Image)"]
    
    # Get current selection and detect changes
    current_selection = st.session_state.get('image_selection_mode', image_options[0])
    
    image_option = st.radio(
        "Content Creation Mode:",
        image_options,
        index=image_options.index(current_selection) if current_selection in image_options else 0,
        help="Select how you want to create your social media content",
        horizontal=False,
        key="image_mode_selector"
    )
    
    # Clear session state if selection changed
    if image_option != current_selection:
        _clear_image_session_state()
        st.session_state.image_selection_mode = image_option
        st.rerun()
    
    image = None
    text_only_mode = False
    
    if image_option == "📝 Text-Only (No Image)":
        text_only_mode = True
        _display_text_only_info()
    elif image_option == "📁 Upload File":
        image = _handle_file_upload()
    elif image_option == "🌐 Use Website Image":
        image = _handle_website_image_selection()
    
    return image, text_only_mode

def _clear_image_session_state():
    """Clear all image-related session state when switching modes."""
    image_keys = [
        'current_image', 'selected_web_image', 'clipboard_image', 
        'uploaded_image', 'website_images'
    ]
    for key in image_keys:
        if key in st.session_state:
            del st.session_state[key]

def _handle_website_image_selection():
    """Handle website image selection."""
    website_analysis = st.session_state.get('website_analysis')
    
    if website_analysis and website_analysis.get('images'):
        # Check if we have a website image selected
        selected_web_image = st.session_state.get('selected_web_image')
        current_image = st.session_state.get('current_image')
        
        st.markdown("### �️ Website Images")
        st.info("🌐 **Website images found!** Select one below to use for your captions.")
        
        images = website_analysis['images']
        
        # Create a grid layout for better display
        cols = st.columns(min(3, len(images)))
        
        for i, img_data in enumerate(images):
            col_idx = i % 3
            with cols[col_idx]:
                try:
                    # Load and display the image
                    response = requests.get(img_data['url'], timeout=10)
                    if response.status_code == 200:
                        web_image = Image.open(io.BytesIO(response.content))
                        st.image(web_image, caption=f"Image {i+1}", use_container_width=True)
                        
                        # Show description
                        description = img_data.get('description', 'Website image')
                        if len(description) > 60:
                            description = description[:60] + "..."
                        st.caption(description)
                        
                        # Check if this image is currently selected
                        is_selected = (selected_web_image == i and current_image is not None)
                        
                        # Button styling based on selection
                        if is_selected:
                            # Show as selected with primary styling and checkmark
                            st.button(f"✅ Use Image {i+1} (Selected)", key=f"selected_web_img_{i}", type="primary", use_container_width=True, disabled=False)
                            st.success("✓ Currently using this image")
                        else:
                            if st.button(f"Use Image {i+1}", key=f"select_web_img_{i}", use_container_width=True):
                                # Set the selection
                                st.session_state.current_image = web_image
                                st.session_state.selected_web_image = i
                                # Force a rerun to update the UI
                                st.rerun()
                    else:
                        st.warning(f"⚠️ Could not load Image {i+1}")
                        st.write(f"**Description:** {img_data.get('description', 'Website image')}")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not load Image {i+1}")
                    st.caption(f"URL: {img_data['url'][:50]}...")
        
        # Show selection status
        if selected_web_image is not None:
            st.success(f"🎯 **Currently selected:** Website Image {selected_web_image + 1}")
        
        # Return the currently selected image if any
        return st.session_state.get('current_image')
    else:
        st.info("🌐 **No website images available**\n\nAnalyze a website in the 'Website Analysis' tab to find images.")
        return None

def _display_text_only_info():
    """Display information about text-only mode."""
    st.info("🎯 **Text-Only Mode**\n\nCaptions will be generated based purely on business information and website context without referencing any image.")
    
    st.markdown("""
    **Perfect for:**
    • Inspirational quotes
    • Business announcements
    • Service highlights
    • Company culture posts
    """)

def _handle_file_upload():
    """Handle file upload for images."""
    # Use a unique key to prevent conflicts
    uploaded_file = st.file_uploader(
        "Choose an image for your social media post",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload a high-quality photo for best caption results",
        key="main_file_uploader"
    )
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            # Clear any previous images
            st.session_state.current_image = image
            st.session_state.uploaded_image = uploaded_file.name
            _display_image_preview(image, uploaded_file)
            return image
        except Exception as e:
            st.error(f"❌ Error loading image: {str(e)}")
            return None
    
    # Show current image if it exists and no new upload
    elif st.session_state.get('current_image') and st.session_state.get('uploaded_image'):
        st.info("✅ Image already uploaded. Upload a new file to replace it.")
        _display_image_preview(st.session_state.current_image, None)
        return st.session_state.current_image
    
    return None

def _display_image_preview(image, uploaded_file):
    """Display image preview with information."""
    col_preview, col_info = st.columns([2, 1])
    with col_preview:
        st.image(image, caption="Your uploaded image", use_container_width=True)
    with col_info:
        st.markdown("**Image Info:**")
        st.write(f"📐 Size: {image.size[0]} x {image.size[1]}")
        st.write(f"🎨 Mode: {image.mode}")
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / 1024
            st.write(f"💾 Size: {file_size:.1f} KB")
        else:
            st.write("💾 Size: Already loaded")

def _handle_business_information():
    """Handle business information input."""
    st.subheader("🏢 Business Details")
    
    # Get default values
    default_business, default_website = _get_default_business_info()
    
    business_input = st.text_input(
        "Business Type/Company Name",
        value=default_business,
        placeholder="e.g., Italian restaurant, fitness studio, tech company",
        help="Describe your business or enter the company name"
    )
    
    website_url = st.text_input(
        "Company Website (Optional)",
        value=default_website,
        placeholder="e.g., https://yourcompany.com",
        help="Website URL for enhanced brand context"
    )
    
    # Quick category selector
    business_input = _handle_quick_category_selection(business_input)
    
    return business_input, website_url

def _get_default_business_info():
    """Get default business information from loaded profile or template."""
    default_business = ""
    default_website = ""
    
    if st.session_state.get('selected_company_profile'):
        profile = st.session_state.selected_company_profile
        default_business = profile.get('business_input', '')
        default_website = profile.get('website_url', '')
    
    return default_business, default_website

def _handle_quick_category_selection(business_input):
    """Handle quick business category selection."""
    st.markdown("**Or select category:**")
    quick_categories = [
        "Restaurant", "Fitness Center", "Retail Store", "Professional Service",
        "Tech Company", "Healthcare", "Beauty Salon", "Real Estate", "Other"
    ]
    
    selected_category = st.selectbox(
        "Business Category",
        ["Select category..."] + quick_categories,
        help="Quick selection for common business types"
    )
    
    if selected_category != "Select category..." and not business_input:
        business_input = selected_category
        st.session_state.auto_business = selected_category
    
    return business_input

def _store_tab_values(values):
    """Store tab values in session state for cross-tab access."""
    for key, value in values.items():
        st.session_state[f'temp_{key}'] = value

def _clear_editing_mode():
    """Clear editing mode session state."""
    keys_to_clear = ['editing_company', 'editing_profile', 'selected_company_profile', 'selected_company_name']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def _clear_loaded_profile():
    """Clear loaded profile session state."""
    keys_to_clear = ['selected_company_profile', 'selected_company_name']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# === Streamlit Main Application ===
def main():
    """Main application function."""
    # Check authentication first
    if not check_password():
        return
    
    # Initialize session state
    initialize_session_state()
    
    # Display page header
    display_page_header()
    
    # Show documentation popup if requested
    show_documentation_popup()
    
    # Show feedback popup if requested
    show_feedback_popup()
    
    # Create enhanced sidebar (with logout option)
    template_config = create_advanced_sidebar()
    show_logout_option()
    
    # Single Page Layout - All inputs and outputs on one page
    handle_single_page_layout(template_config)

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
            clear_all_session_data()
            st.success("✅ App reset successfully!")
            st.rerun()
    
    with col_footer4:
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em; padding: 10px;'>
        🚀 Adcellerant Social Caption Generator<br>
        AI-Powered Social Media Content Creation
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    show_app_footer()
