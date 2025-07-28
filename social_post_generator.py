#!/usr/bin/env python3
"""
Adcellerant Social Caption Generator
AI-Powered Social Media Caption Generator with Advanced Website Analysis
"""

# Standard library imports
import os
import base64
import hashlib
import io
import json
import zipfile
from datetime import datetime

# Third-party imports
import requests
import streamlit as st
import streamlit.components.v1
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from urllib.parse import urljoin, urlparse

# Optional imports
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Check for image clipboard support
try:
    from PIL import ImageGrab
    # Test if clipboard functionality works
    try:
        ImageGrab.grabclipboard()
        IMAGE_CLIPBOARD_AVAILABLE = True
    except:
        IMAGE_CLIPBOARD_AVAILABLE = False
except ImportError:
    IMAGE_CLIPBOARD_AVAILABLE = False

# Web clipboard support (always available in browsers)
WEB_CLIPBOARD_AVAILABLE = True

# === Constants ===
COMPANY_DATA_FILE = "company_profiles.json"
USED_CAPTIONS_FILE = "used_captions.json"
APP_PASSWORD = os.getenv("APP_PASSWORD", "adcellerant2025")  # Change this!

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
            # Clear password session
            for key in list(st.session_state.keys()):
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
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {}
    except Exception as e:
        st.error(f"Error loading used captions: {str(e)}")
        return {}

def save_used_captions(used_captions):
    """Save used captions to JSON file."""
    try:
        with open(USED_CAPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(used_captions, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving used captions: {str(e)}")
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

# === Company Directory Management ===
def load_company_profiles():
    """Load saved company profiles from JSON file with error handling."""
    try:
        if os.path.exists(COMPANY_DATA_FILE):
            with open(COMPANY_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        st.error(f"Error loading company profiles: {str(e)}")
        return {}
    except Exception as e:
        st.error(f"Unexpected error loading profiles: {str(e)}")
        return {}

def save_company_profiles(profiles):
    """Save company profiles to JSON file with error handling."""
    try:
        with open(COMPANY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving company profiles: {str(e)}")
        return False

def save_company_profile(company_name, profile_data):
    """Save a single company profile with timestamp tracking."""
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

def clear_all_session_data():
    """Clear all session state data for starting over."""
    keys_to_clear = [
        'current_image', 'generated_captions', 'website_analysis', 
        'selected_web_image', 'auto_business', 'selected_company_profile',
        'selected_company_name', 'editing_company', 'editing_profile', 
        'show_save_options'
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
                     caption_length="Medium (4-6 sentences)", text_only_mode=False):
    """Main function to generate social media captions."""
    try:
        # Analyze website if URL provided
        website_info = _get_website_info(website_url)
        
        # Create prompt based on available information
        prompt = _create_caption_prompt(
            website_info, business_input, caption_style, 
            caption_length, include_cta, text_only_mode
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
                          caption_length, include_cta, text_only_mode):
    """Create the prompt for caption generation based on available information."""
    # Style and length mappings
    style_instructions = _get_style_instructions()
    length_map = _get_length_mapping()
    
    cta_instruction = _get_cta_instruction(include_cta)
    
    if website_info and isinstance(website_info, dict):
        return _create_enhanced_prompt(
            website_info, business_input, style_instructions, 
            length_map, caption_style, caption_length, 
            cta_instruction, text_only_mode
        )
    else:
        return _create_basic_prompt(
            business_input, style_instructions, length_map, 
            caption_style, caption_length, cta_instruction, text_only_mode
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

def _create_enhanced_prompt(website_info, business_input, style_instructions, 
                           length_map, caption_style, caption_length, 
                           cta_instruction, text_only_mode):
    """Create enhanced prompt using website information."""
    company_name = website_info.get('title', business_input).split('|')[0].strip()
    company_description = website_info.get('description', '')
    services = ', '.join(website_info.get('services', [])[:3])
    about_text = website_info.get('about_text', '')
    
    base_requirements = f"""Requirements:
- Each caption should be exactly {length_map[caption_length]} long
- NO emojis or hashtags
- Style: {style_instructions[caption_style]}
- Make them ready to post on Instagram, Facebook, or LinkedIn
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
                        caption_style, caption_length, cta_instruction, text_only_mode):
    """Create basic prompt without website information."""
    business_type = business_input if business_input.strip() else "business"
    
    base_requirements = f"""Requirements:
- Each caption should be exactly {length_map[caption_length]} long
- NO emojis or hashtags
- Style: {style_instructions[caption_style]}
- Include storytelling elements that connect with the audience
- Ready for Instagram, Facebook, or LinkedIn
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
                else:
                    st.info("No saved companies yet. Create some posts and save company profiles!")
        else:
            st.info("💡 **No saved companies yet**\n\nAfter generating captions, you'll see an option to save the company profile for future use.")
        
        st.markdown("---")
        
        # Quick Start Guide
        st.markdown("### 🎯 Quick Start Guide")
        
        with st.expander("📋 How to Use", expanded=False):
            st.markdown("""
            **Step 1:** Choose image source or text-only
            **Step 2:** Enter business information  
            **Step 3:** Customize style & settings
            **Step 4:** Generate captions
            **Step 5:** Save company profile (optional)
            """)
        
        with st.expander("💡 Pro Tips"):
            st.markdown("""
            • **Save companies** for faster future posts
            • **Text-only mode** for quick content creation
            • **Load saved profiles** to auto-fill everything
            • **Batch processing** for multiple images
            • **Premium model** for best results
            """)
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            • **Website blocked?** Try without URL
            • **Image too large?** Resize before upload
            • **Slow generation?** Use mini model
            • **Need fresh start?** Use "Start Over" button
            """)
        
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
        
        # Show option to clear used captions
        if usage_stats['total_used'] > 0:
            with st.expander("🗑️ Manage Used Captions"):
                st.warning(f"You have {usage_stats['total_used']} captions marked as used")
                if st.button("🔄 Clear All Used Captions", type="secondary"):
                    if os.path.exists(USED_CAPTIONS_FILE):
                        os.remove(USED_CAPTIONS_FILE)
                        st.success("✅ Cleared all used caption records")
                        st.rerun()
                st.caption("⚠️ This will reset duplicate detection")
        
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

# === Main Application Functions ===
def initialize_session_state():
    """Initialize session state variables."""
    default_values = {
        'generated_captions': None,
        'current_image': None,
        'website_analysis': None,
        'captions_generated': 0
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def display_page_header():
    """Display the main page header with metrics."""
    col_title, col_metrics = st.columns([3, 1])
    
    with col_title:
        st.title("🚀 Adcellerant Social Caption Generator")
        st.markdown("**AI-Powered Social Media Caption Generator with Advanced Website Analysis**")
    
    with col_metrics:
        st.metric("🎯 Captions Created", st.session_state.captions_generated)

def create_main_tabs():
    """Create and return the main application tabs."""
    return st.tabs([
        "📸 Image & Business", 
        "🎨 Style Settings", 
        "🌐 Website Analysis", 
        "📱 Generated Captions", 
        "🔄 Batch Processing"
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
    
    # Build options list based on available functionality
    image_options = ["📁 Upload File"]
    
    # Add clipboard options based on environment
    if IMAGE_CLIPBOARD_AVAILABLE:
        image_options.append("📋 Paste from System Clipboard")
    
    if WEB_CLIPBOARD_AVAILABLE:
        image_options.append("🌐 Paste from Web Clipboard")
    
    image_options.extend(["🔗 Use Website Image", "📝 Text-Only (No Image)"])
    
    image_option = st.radio(
        "Content Creation Mode:",
        image_options,
        help="Select how you want to create your social media content",
        horizontal=False
    )
    
    image = None
    text_only_mode = False
    
    if image_option == "📝 Text-Only (No Image)":
        text_only_mode = True
        _display_text_only_info()
    elif image_option == "📁 Upload File":
        image = _handle_file_upload()
    elif image_option == "📋 Paste from System Clipboard":
        image = _handle_clipboard_paste()
    elif image_option == "🌐 Paste from Web Clipboard":
        image = _handle_web_clipboard_paste()
    elif image_option == "🔗 Use Website Image":
        st.info("📝 Enter a website URL in the 'Website Analysis' tab to see available images.")
    
    return image, text_only_mode

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
    uploaded_file = st.file_uploader(
        "Choose an image for your social media post",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload a high-quality photo for best caption results"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.current_image = image
        _display_image_preview(image, uploaded_file)
        return image
    
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
        file_size = len(uploaded_file.getvalue()) / 1024
        st.write(f"💾 Size: {file_size:.1f} KB")

def _handle_clipboard_paste():
    """Handle system clipboard paste functionality."""
    if IMAGE_CLIPBOARD_AVAILABLE:
        col_btn, col_status = st.columns([1, 1])
        with col_btn:
            if st.button("📋 Paste Image", help="Click after copying an image (Ctrl+C)", type="primary"):
                try:
                    from PIL import ImageGrab
                    clipboard_image = ImageGrab.grabclipboard()
                    
                    if clipboard_image:
                        st.session_state.current_image = clipboard_image
                        st.image(clipboard_image, caption="Image from clipboard", use_container_width=True)
                        st.success("✅ Image successfully pasted!")
                        return clipboard_image
                    else:
                        st.warning("⚠️ No image found in clipboard.")
                except Exception as e:
                    st.error(f"❌ Clipboard error: {str(e)}")
        
        with col_status:
            st.info("💡 **How to paste:**\n1. Copy image (Ctrl+C)\n2. Click 'Paste Image' button")
    else:
        st.warning("⚠️ **System clipboard not available in cloud environment.**")
        st.info("💡 **Try 'Web Clipboard' option instead**")
    
    return None

def _handle_web_clipboard_paste():
    """Handle web-based clipboard paste functionality."""
    st.info("🌐 **Web Clipboard Alternative**")
    st.markdown("Since direct clipboard access isn't available in web browsers, here are the best alternatives:")
    
    # Create columns for different methods
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📸 **Method 1: Screenshot & Upload**")
        st.markdown("""
        1. **Take screenshot** (Windows: Win+Shift+S, Mac: Cmd+Shift+4)
        2. **Save image** to your computer  
        3. **Use Upload File** option above
        """)
        
        if st.button("📁 Switch to Upload File", type="primary"):
            st.session_state.clipboard_redirect = True
            st.rerun()
    
    with col2:
        st.markdown("### 🖱️ **Method 2: Drag & Drop**")
        st.markdown("""
        1. **Copy/screenshot** your image
        2. **Save to desktop** or downloads
        3. **Drag the file** into the upload area above
        """)
        
        st.info("💡 **Pro Tip:** Most modern browsers support dragging images directly into file upload areas!")
    
    # Advanced users section
    with st.expander("🔧 **For Advanced Users**"):
        st.markdown("""
        **Browser Extensions:**
        • Install clipboard manager extensions
        • Use screenshot tools with direct upload
        • Browser developer tools for base64 conversion
        
        **Alternative Tools:**
        • Lightshot, Greenshot, or similar screenshot tools
        • Online image converters
        • Cloud storage integration (Google Drive, Dropbox)
        """)
    
    st.warning("💡 **Note:** Web browsers restrict direct clipboard access for security. The upload method is the most reliable for web applications.")
    
    return None

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
    
    # Create enhanced sidebar (with logout option)
    template_config = create_advanced_sidebar()
    show_logout_option()
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5 = create_main_tabs()
    
    # Tab 1: Image & Business
    with tab1:
        image, business_input, website_url, text_only_mode = handle_image_business_tab()
    
    # Tab 2: Style Settings (keeping existing implementation for now)
    with tab2:
        st.header("🎨 Caption Style & Customization")
        
        style_col1, style_col2 = st.columns(2)
        
        with style_col1:
            # Pre-fill from loaded profile or template
            default_style = "Professional"
            default_length = 1  # Medium
            default_premium = False
            default_cta = True
            
            if st.session_state.get('selected_company_profile'):
                profile = st.session_state.selected_company_profile
                default_style = profile.get('caption_style', 'Professional')
                length_options = ["Short (3-4 sentences)", "Medium (4-6 sentences)", "Long (6+ sentences)"]
                try:
                    default_length = length_options.index(profile.get('caption_length', 'Medium (4-6 sentences)'))
                except ValueError:
                    default_length = 1
                default_premium = profile.get('use_premium_model', False)
                default_cta = profile.get('include_cta', True)
            elif template_config:
                default_style = template_config['tone']
            
            caption_style = st.selectbox(
                "🎭 Caption Style",
                ["Professional", "Casual & Friendly", "Inspirational", "Educational", "Promotional"],
                index=["Professional", "Casual & Friendly", "Inspirational", "Educational", "Promotional"].index(default_style),
                help="Choose the tone and style for your captions"
            )
            
            caption_length = st.selectbox(
                "📏 Caption Length",
                ["Short (3-4 sentences)", "Medium (4-6 sentences)", "Long (6+ sentences)"],
                index=default_length,
                help="Preferred length for generated captions"
            )
            
            use_premium_model = st.checkbox(
                "⭐ Use Premium Model (GPT-4o)",
                value=default_premium,
                help="Higher quality results but costs more. Uncheck for cost-effective GPT-4o-mini."
            )
        
        with style_col2:
            include_cta = st.checkbox(
                "🎯 Include Call-to-Action",
                value=default_cta,
                help="Add subtle calls-to-action in captions"
            )
            
            # Advanced customization options
            st.markdown("**🔧 Advanced Options:**")
            
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
                "Focus Keywords",
                value=default_focus,
                placeholder="e.g., organic, handmade, premium",
                help="Keywords to emphasize in captions"
            )
            
            avoid_words = st.text_input(
                "Words to Avoid",
                value=default_avoid,
                placeholder="e.g., cheap, basic, generic",
                help="Words to avoid in captions"
            )
            
            target_audience = st.selectbox(
                "Target Audience",
                ["General", "Young Adults (18-35)", "Professionals", "Families", "Seniors", "Local Community"],
                index=default_audience,
                help="Tailor captions to specific audience"
            )
            
            # Store in session state for cross-tab access
            st.session_state.temp_caption_style = caption_style
            st.session_state.temp_caption_length = caption_length
            st.session_state.temp_use_premium_model = use_premium_model
            st.session_state.temp_include_cta = include_cta
            st.session_state.temp_focus_keywords = focus_keywords
            st.session_state.temp_avoid_words = avoid_words
            st.session_state.temp_target_audience = target_audience
    
    with tab3:
        st.header("🌐 Website Analysis & Context")
        
        analysis_col1, analysis_col2 = st.columns([2, 1])
        
        with analysis_col1:
            # Pre-fill website URL from loaded profile
            default_website_url = ""
            if st.session_state.get('selected_company_profile'):
                default_website_url = st.session_state.selected_company_profile.get('website_url', '')
            
            website_url = st.text_input(
                "🔗 Company Website URL",
                value=default_website_url,
                placeholder="https://yourcompany.com or yourcompany.com",
                help="Provide website URL for enhanced, brand-specific captions"
            )
            
            if website_url and website_url.strip():
                if st.button("🔍 Analyze Website", type="primary"):
                    show_progress_indicator(1, 3, "Fetching main page")
                    website_info = analyze_website_with_spinner(website_url.strip())
                    st.session_state.website_analysis = website_info
                    
                    if website_info:
                        show_progress_indicator(2, 3, "Analyzing content")
                        st.success(f"✅ Analysis complete! Found {len(website_info.get('pages_analyzed', []))} pages")
                        
                        show_progress_indicator(3, 3, "Processing complete")
                        
                        # Display analysis summary
                        st.markdown("### 📊 Website Analysis Summary")
                        
                        summary_col1, summary_col2, summary_col3 = st.columns(3)
                        
                        with summary_col1:
                            st.metric("Pages Analyzed", len(website_info.get('pages_analyzed', [])))
                        
                        with summary_col2:
                            st.metric("Services Found", len(website_info.get('services', [])))
                        
                        with summary_col3:
                            st.metric("Images Found", len(website_info.get('images', [])))
                        
                        # Show detailed analysis
                        with st.expander("📄 Detailed Analysis"):
                            if website_info.get('about_text'):
                                st.markdown("**About Text:**")
                                st.text_area("Company Description", website_info['about_text'][:500] + "..." if len(website_info['about_text']) > 500 else website_info['about_text'], height=100, disabled=True)
                            
                            if website_info.get('services'):
                                st.markdown("**Services/Products:**")
                                for i, service in enumerate(website_info['services'][:5], 1):
                                    st.write(f"{i}. {service}")
                            
                            st.markdown("**Pages Analyzed:**")
                            for i, page in enumerate(website_info.get('pages_analyzed', []), 1):
                                st.write(f"{i}. {page}")
            
            # Website image selection - enhanced UI
            if st.session_state.get('website_analysis') and st.session_state.website_analysis.get('images'):
                st.markdown("### 🖼️ Website Images")
                website_info = st.session_state.website_analysis
                
                # Check if user has already selected an image or is in text-only mode
                has_user_image = st.session_state.get('current_image') is not None
                
                if has_user_image:
                    st.info("ℹ️ Your uploaded/pasted image takes priority. Website images shown for reference:")
                else:
                    st.write("Select an image from the company website:")
                
                # Create a grid of images
                cols = st.columns(min(3, len(website_info['images'])))
                
                for i, img_info in enumerate(website_info['images']):
                    col_idx = i % 3
                    with cols[col_idx]:
                        try:
                            img_response = requests.get(img_info['url'], timeout=5)
                            if img_response.status_code == 200:
                                web_image = Image.open(io.BytesIO(img_response.content))
                                st.image(web_image, caption=f"Image {i+1}", use_container_width=True)
                                
                                # Allow selection if no user image is already selected
                                if not has_user_image:
                                    if st.button(f"✅ Use This Image", key=f"web_img_{i}", use_container_width=True):
                                        st.session_state.current_image = web_image
                                        st.session_state.selected_web_image = i
                                        st.success(f"Selected website image {i+1}")
                                        st.rerun()
                                
                                st.caption(img_info['description'][:50] + "..." if len(img_info['description']) > 50 else img_info['description'])
                        except Exception:
                            st.warning(f"⚠️ Could not load image {i+1}")
        
        with analysis_col2:
            st.markdown("### 📈 Analysis Tips")
            st.info("""
            **For best results:**
            • Use the company's main website
            • Ensure site is publicly accessible
            • Check that pages load properly
            • Larger sites give better context
            """)
            
            if st.session_state.get('website_analysis'):
                st.markdown("### ✅ Analysis Status")
                st.success("Website analysis complete!")
                
                if st.button("🔄 Re-analyze Website"):
                    st.session_state.website_analysis = None
                    st.rerun()
    
    with tab4:
        st.header("📱 Generate & Download Captions")
        
        # Generation section
        generation_ready = ((st.session_state.get('current_image') is not None or text_only_mode) and 
                          business_input and business_input.strip())
        
        if not generation_ready:
            st.warning("⚠️ Please complete the following to generate captions:")
            if not st.session_state.get('current_image') and not text_only_mode:
                st.write("• 📸 Select an image or choose text-only mode")
            if not business_input or not business_input.strip():
                st.write("• 🏢 Enter business information")
        else:
            if text_only_mode:
                st.success("✅ Ready to generate text-only captions!")
            else:
                st.success("✅ Ready to generate image-based captions!")
            
            # Show current configuration
            with st.expander("📋 Current Configuration"):
                config_col1, config_col2 = st.columns(2)
                with config_col1:
                    st.write(f"**Business:** {business_input}")
                    st.write(f"**Style:** {caption_style}")
                    st.write(f"**Length:** {caption_length}")
                    st.write(f"**Mode:** {'Text-Only' if text_only_mode else 'Image-Based'}")
                with config_col2:
                    st.write(f"**Model:** {'GPT-4o (Premium)' if use_premium_model else 'GPT-4o-mini'}")
                    st.write(f"**CTA:** {'Yes' if include_cta else 'No'}")
                    st.write(f"**Website:** {'Analyzed' if st.session_state.get('website_analysis') else 'Not used'}")
                    if focus_keywords:
                        st.write(f"**Focus:** {focus_keywords}")
            
            # Generate button
            generate_button_text = "🚀 Generate Text-Only Captions" if text_only_mode else "🚀 Generate Social Media Captions"
            
            if st.button(generate_button_text, type="primary", use_container_width=True):
                show_progress_indicator(1, 4, "Preparing context and settings")
                
                # Get variables from current tab context
                if 'business_input' not in locals():
                    business_input = st.session_state.get('temp_business_input', '')
                if 'website_url' not in locals():
                    website_url = st.session_state.get('temp_website_url', '')
                if 'caption_style' not in locals():
                    caption_style = st.session_state.get('temp_caption_style', 'Professional')
                if 'caption_length' not in locals():
                    caption_length = st.session_state.get('temp_caption_length', 'Medium (4-6 sentences)')
                if 'use_premium_model' not in locals():
                    use_premium_model = st.session_state.get('temp_use_premium_model', False)
                if 'include_cta' not in locals():
                    include_cta = st.session_state.get('temp_include_cta', True)
                if 'focus_keywords' not in locals():
                    focus_keywords = st.session_state.get('temp_focus_keywords', '')
                if 'target_audience' not in locals():
                    target_audience = st.session_state.get('temp_target_audience', 'General')
                if 'text_only_mode' not in locals():
                    text_only_mode = st.session_state.get('temp_text_only_mode', False)
                
                # Build enhanced prompt with all customizations
                enhanced_business_input = business_input
                if focus_keywords:
                    enhanced_business_input += f" (focus on: {focus_keywords})"
                if target_audience != "General":
                    enhanced_business_input += f" (targeting: {target_audience})"
                
                show_progress_indicator(2, 4, f"Generating {'text-only ' if text_only_mode else ''}captions with AI")
                
                # Use current image or None for text-only mode
                final_image = None if text_only_mode else st.session_state.get('current_image')
                
                result = generate_captions(
                    final_image, 
                    enhanced_business_input, 
                    website_url, 
                    use_premium_model,
                    caption_style,
                    include_cta,
                    caption_length,
                    text_only_mode
                )
                
                if result:
                    show_progress_indicator(3, 4, "Processing results")
                    st.session_state.generated_captions = result
                    st.session_state.captions_generated += 1
                    
                    # Store current settings for potential saving
                    st.session_state.current_settings = {
                        'business_input': business_input,
                        'website_url': website_url,
                        'caption_style': caption_style,
                        'caption_length': caption_length,
                        'use_premium_model': use_premium_model,
                        'include_cta': include_cta,
                        'focus_keywords': focus_keywords,
                        'avoid_words': st.session_state.get('temp_avoid_words', ''),
                        'target_audience': target_audience,
                        'text_only_mode': text_only_mode
                    }
                    
                    show_progress_indicator(4, 4, "Captions generated successfully!")
                    st.success("✅ Social media captions generated successfully!")
        
        # Display generated captions if available
        if st.session_state.get('generated_captions'):
            st.markdown("---")
            st.header("📝 Your Generated Captions")
            st.success("🎉 Captions generated successfully! Ready to copy and use.")
            
            # Enhanced caption display
            captions = st.session_state.generated_captions.split('\n\n')
            
            for i, caption in enumerate(captions):
                if caption.strip():
                    with st.container():
                        # Check if caption was previously used
                        is_duplicate, duplicate_info = is_caption_duplicate(caption.strip())
                        
                        caption_header_col, copy_col, mark_used_col = st.columns([3, 1, 1])
                        
                        with caption_header_col:
                            if is_duplicate:
                                st.subheader(f"⚠️ Caption {i+1} (Previously Used)")
                                st.warning(f"🔄 Similar caption used on {duplicate_info['used_date'][:10]} for {duplicate_info.get('business', 'Unknown')}")
                            else:
                                st.subheader(f"✨ Caption {i+1} (New)")
                        
                        with copy_col:
                            if CLIPBOARD_AVAILABLE:
                                if st.button(f"📋 Copy", key=f"copy_btn_{i}", help=f"Copy caption {i+1} to clipboard"):
                                    pyperclip.copy(caption.strip())
                                    st.success("✅ Copied!")
                        
                        with mark_used_col:
                            # Check if caption is already marked as used
                            is_currently_used = is_caption_duplicate(caption.strip())[0]
                            
                            if is_currently_used:
                                # Show "Unmark" button if already used
                                if st.button(f"🔄 Unmark", key=f"unmark_used_{i}", help=f"Remove caption {i+1} from usage history"):
                                    if unmark_caption_as_used(caption.strip()):
                                        st.success("✅ Removed from usage history!")
                                    else:
                                        st.error("❌ Failed to remove from history")
                                    st.rerun()
                            else:
                                # Show "Mark Used" button if not used
                                if st.button(f"✅ Mark Used", key=f"mark_used_{i}", help=f"Mark caption {i+1} as used"):
                                    mark_caption_as_used(caption.strip(), business_input)
                                    st.success("📝 Marked as used!")
                                    st.rerun()
                        
                        # Caption with enhanced multi-line styling
                        st.markdown("**Caption Text:**")
                        # Use text_area for multi-line display with proper height
                        st.text_area(
                            label="",
                            value=caption.strip(),
                            height=120,
                            key=f"caption_display_{i}",
                            help="Caption text - automatically sized for readability",
                            label_visibility="collapsed"
                        )
                        
                        # Character count and social media suitability
                        char_count = len(caption.strip())
                        
                        suitability_col1, suitability_col2, suitability_col3 = st.columns(3)
                        with suitability_col1:
                            fb_suitable = "✅" if char_count <= 500 else "⚠️"
                            st.caption(f"Facebook: {fb_suitable} ({char_count}/500)")
                        with suitability_col2:
                            ig_suitable = "✅" if char_count <= 400 else "⚠️"  
                            st.caption(f"Instagram: {ig_suitable} ({char_count}/400)")
                        with suitability_col3:
                            li_suitable = "✅" if char_count <= 700 else "⚠️"
                            st.caption(f"LinkedIn: {li_suitable} ({char_count}/700)")
                        
                        st.markdown("---")
            
            # Download section with enhanced options and save company option
            st.subheader("💾 Download & Save Options")
            
            download_col1, download_col2, download_col3, save_col = st.columns(4)
            
            with download_col1:
                st.download_button(
                    label="📄 Download All Captions",
                    data=st.session_state.generated_captions,
                    file_name=f"social_captions_{business_input.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with download_col2:
                if st.session_state.get('current_image') and not text_only_mode:
                    current_date = datetime.now().strftime("%Y%m%d")
                    company_safe_name = business_input.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    
                    img_buffer = io.BytesIO()
                    st.session_state.current_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    st.download_button(
                        label="🖼️ Download Image",
                        data=img_buffer.getvalue(),
                        file_name=f"{company_safe_name}_{current_date}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                else:
                    st.info("💡 Text-only mode - no image to download")
            
            with download_col3:
                # Create combined package
                combined_content = f"Social Media Captions for {business_input}\n"
                combined_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                combined_content += f"Style: {caption_style}\n"
                combined_content += f"Length: {caption_length}\n"
                combined_content += f"Mode: {'Text-Only' if text_only_mode else 'Image-Based'}\n\n"
                combined_content += "=" * 50 + "\n\n"
                combined_content += st.session_state.generated_captions
                
                st.download_button(
                    label="📦 Download Package",
                    data=combined_content,
                    file_name=f"caption_package_{business_input.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with save_col:
                # Company profile save option - enhanced for editing mode
                save_button_text = "💾 Update Company" if st.session_state.get('editing_company') else "💾 Save Company"
                save_help_text = "Update the existing company profile" if st.session_state.get('editing_company') else "Save this company profile for future use"
                
                if st.button(save_button_text, use_container_width=True, help=save_help_text):
                    if st.session_state.get('current_settings'):
                        settings = st.session_state.current_settings
                        
                        # Create profile data
                        profile_data = {
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
                            'captions_generated_count': 1,
                            'website_analysis': st.session_state.get('website_analysis')
                        }
                        
                        # Check if we're in editing mode
                        if st.session_state.get('editing_company'):
                            # Show options to save
                            st.session_state.show_save_options = True
                        else:
                            # Use business name as company name for new saves
                            company_name = settings.get('business_input', 'Unknown Company')
                            
                            if save_company_profile(company_name, profile_data):
                                st.success(f"✅ Saved company profile: {company_name}")
                            else:
                                st.error("❌ Failed to save company profile")
                    else:
                        st.warning("⚠️ No settings to save. Generate captions first.")
                
                # Show save options when editing
                if st.session_state.get('show_save_options') and st.session_state.get('editing_company'):
                    with st.expander("💾 Save Options", expanded=True):
                        save_option = st.radio(
                            "How would you like to save?",
                            ["Overwrite existing company", "Save as new company"],
                            horizontal=True
                        )
                        
                        if save_option == "Overwrite existing company":
                            original_name = st.session_state.editing_company
                            st.write(f"**Overwrite:** {original_name}")
                            
                            if st.button("✅ Confirm Overwrite", type="primary"):
                                if st.session_state.get('current_settings'):
                                    settings = st.session_state.current_settings
                                    profile_data = {
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
                                        'captions_generated_count': 1,
                                        'website_analysis': st.session_state.get('website_analysis')
                                    }
                                    
                                    if save_company_profile(original_name, profile_data):
                                        st.success(f"✅ Updated company profile: {original_name}")
                                        # Clear editing mode
                                        for key in ['editing_company', 'editing_profile', 'show_save_options']:
                                            if key in st.session_state:
                                                del st.session_state[key]
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update company profile")
                        
                        elif save_option == "Save as new company":
                            new_company_name = st.text_input(
                                "New Company Name:",
                                value=st.session_state.get('current_settings', {}).get('business_input', ''),
                                help="Enter a name for the new company profile"
                            )
                            
                            if new_company_name and st.button("✅ Save as New", type="primary"):
                                if st.session_state.get('current_settings'):
                                    settings = st.session_state.current_settings
                                    profile_data = {
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
                                        'captions_generated_count': 1,
                                        'website_analysis': st.session_state.get('website_analysis')
                                    }
                                    
                                    if save_company_profile(new_company_name, profile_data):
                                        st.success(f"✅ Saved new company profile: {new_company_name}")
                                        # Clear editing mode
                                        for key in ['editing_company', 'editing_profile', 'show_save_options']:
                                            if key in st.session_state:
                                                del st.session_state[key]
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to save new company profile")
                        
                        if st.button("❌ Cancel Save", type="secondary"):
                            st.session_state.show_save_options = False
                            st.rerun()
    
    with tab5:
        st.header("🔄 Batch Processing")
        st.markdown("Generate captions for multiple images at once - perfect for content planning!")
        
        batch_col1, batch_col2 = st.columns([2, 1])
        
        with batch_col1:
            st.subheader("📁 Upload Multiple Images")
            
            batch_files = st.file_uploader(
                "Choose multiple images for batch processing",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                help="Upload 2-10 images for batch caption generation"
            )
            
            if batch_files:
                st.success(f"✅ {len(batch_files)} images uploaded")
                
                # Show image preview grid
                if len(batch_files) <= 6:
                    cols = st.columns(min(3, len(batch_files)))
                    for i, uploaded_file in enumerate(batch_files):
                        col_idx = i % 3
                        with cols[col_idx]:
                            image = Image.open(uploaded_file)
                            st.image(image, caption=f"Image {i+1}", use_container_width=True)
                            st.caption(f"📏 {image.size[0]}x{image.size[1]}")
                else:
                    st.info(f"📊 {len(batch_files)} images ready for processing (preview limited to first 6)")
                    cols = st.columns(3)
                    for i in range(min(6, len(batch_files))):
                        col_idx = i % 3
                        with cols[col_idx]:
                            image = Image.open(batch_files[i])
                            st.image(image, caption=f"Image {i+1}", use_container_width=True)
        
        with batch_col2:
            st.subheader("⚙️ Batch Settings")
            
            # Reuse business input from tab1
            if 'business_input' in locals() and business_input:
                st.write(f"**Business:** {business_input}")
            else:
                batch_business = st.text_input(
                    "Business Type",
                    placeholder="e.g., restaurant, fitness studio",
                    help="Same business info will be used for all images"
                )
            
            batch_style = st.selectbox(
                "Caption Style for All",
                ["Professional", "Casual & Friendly", "Inspirational", "Educational", "Promotional"],
                help="All images will use this style"
            )
            
            batch_length = st.selectbox(
                "Caption Length for All", 
                ["Short (3-4 sentences)", "Medium (4-6 sentences)", "Long (6+ sentences)"],
                index=1
            )
            
            batch_premium = st.checkbox(
                "Use Premium Model",
                help="Higher quality but more expensive"
            )
            
            # Processing options
            st.markdown("**Processing Options:**")
            
            individual_files = st.checkbox(
                "Generate individual files",
                value=True,
                help="Create separate caption files for each image"
            )
            
            combined_file = st.checkbox(
                "Generate combined file", 
                value=True,
                help="Create one file with all captions"
            )
            
            auto_download = st.checkbox(
                "Auto-download results",
                help="Automatically download files when complete"
            )
        
        # Batch processing execution
        if batch_files and len(batch_files) > 1:
            if len(batch_files) > 10:
                st.warning("⚠️ Batch processing limited to 10 images. Only first 10 will be processed.")
                batch_files = batch_files[:10]
            
            business_for_batch = batch_business if 'batch_business' in locals() and batch_business else business_input if 'business_input' in locals() else ""
            
            if st.button("🚀 Start Batch Processing", type="primary", use_container_width=True):
                if not business_for_batch:
                    st.error("Please enter business information first!")
                else:
                    # Initialize batch results
                    batch_results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Process each image
                    for i, uploaded_file in enumerate(batch_files):
                        status_text.text(f"Processing image {i+1}/{len(batch_files)}: {uploaded_file.name}")
                        progress_bar.progress((i + 1) / len(batch_files))
                        
                        try:
                            # Load image
                            image = Image.open(uploaded_file)
                            
                            # Generate captions
                            result = generate_captions(
                                image,
                                business_for_batch,
                                website_url if 'website_url' in locals() else "",
                                batch_premium,
                                batch_style,
                                True,  # Include CTA
                                batch_length
                            )
                            
                            if result:
                                batch_results.append({
                                    'filename': uploaded_file.name,
                                    'image': image,
                                    'captions': result
                                })
                            
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    
                    # Display results
                    if batch_results:
                        status_text.text(f"✅ Batch processing complete! {len(batch_results)} images processed.")
                        st.balloons()
                        
                        # Update session state
                        if 'captions_generated' not in st.session_state:
                            st.session_state.captions_generated = 0
                        st.session_state.captions_generated += len(batch_results)
                        
                        # Show results summary
                        st.markdown("### 📊 Batch Results Summary")
                        
                        summary_cols = st.columns(4)
                        with summary_cols[0]:
                            st.metric("Images Processed", len(batch_results))
                        with summary_cols[1]:
                            total_captions = len(batch_results) * 3
                            st.metric("Total Captions", total_captions)
                        with summary_cols[2]:
                            avg_length = sum(len(r['captions']) for r in batch_results) / len(batch_results)
                            st.metric("Avg Caption Length", f"{avg_length:.0f} chars")
                        with summary_cols[3]:
                            model_used = "GPT-4o" if batch_premium else "GPT-4o-mini"
                            st.metric("Model Used", model_used)
                        
                        # Display individual results
                        st.markdown("### 📝 Individual Results")
                        
                        for i, result in enumerate(batch_results):
                            with st.expander(f"📸 {result['filename']} - Captions", expanded=i==0):
                                result_col1, result_col2 = st.columns([1, 2])
                                
                                with result_col1:
                                    st.image(result['image'], caption=result['filename'], use_container_width=True)
                                
                                with result_col2:
                                    st.text_area(
                                        f"Captions for {result['filename']}",
                                        value=result['captions'],
                                        height=200,
                                        key=f"batch_caption_{i}"
                                    )
                        
                        # Download options
                        st.markdown("### 💾 Download Batch Results")
                        
                        download_cols = st.columns(3)
                        
                        with download_cols[0]:
                            if individual_files:
                                # Create zip file with individual caption files
                                import zipfile
                                zip_buffer = io.BytesIO()
                                
                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                    for result in batch_results:
                                        filename = f"captions_{result['filename'].split('.')[0]}.txt"
                                        zip_file.writestr(filename, result['captions'])
                                
                                zip_buffer.seek(0)
                                
                                st.download_button(
                                    label="📦 Download Individual Files (ZIP)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"batch_captions_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                        
                        with download_cols[1]:
                            if combined_file:
                                # Create combined file
                                combined_content = f"Batch Social Media Captions\n"
                                combined_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                                combined_content += f"Business: {business_for_batch}\n"
                                combined_content += f"Style: {batch_style}\n"
                                combined_content += f"Images Processed: {len(batch_results)}\n"
                                combined_content += "=" * 60 + "\n\n"
                                
                                for i, result in enumerate(batch_results, 1):
                                    combined_content += f"IMAGE {i}: {result['filename']}\n"
                                    combined_content += "-" * 40 + "\n"
                                    combined_content += result['captions']
                                    combined_content += "\n\n" + "=" * 60 + "\n\n"
                                
                                st.download_button(
                                    label="📄 Download Combined File",
                                    data=combined_content,
                                    file_name=f"batch_captions_combined_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                        
                        with download_cols[2]:
                            # Download all images as ZIP
                            img_zip_buffer = io.BytesIO()
                            
                            with zipfile.ZipFile(img_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for result in batch_results:
                                    img_buffer = io.BytesIO()
                                    result['image'].save(img_buffer, format='PNG')
                                    img_buffer.seek(0)
                                    
                                    filename = f"processed_{result['filename'].split('.')[0]}.png"
                                    zip_file.writestr(filename, img_buffer.getvalue())
                            
                            img_zip_buffer.seek(0)
                            
                            st.download_button(
                                label="🖼️ Download All Images (ZIP)",
                                data=img_zip_buffer.getvalue(),
                                file_name=f"batch_images_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                    else:
                        st.error("❌ No images were successfully processed. Please check your images and try again.")
        
        else:
            st.info("📝 Upload 2 or more images to enable batch processing")
            
            # Batch processing tips
            with st.expander("💡 Batch Processing Tips"):
                st.markdown("""
                **Best Practices:**
                • Upload 2-10 images for optimal processing time
                • Use consistent image quality and size
                • Ensure all images are relevant to your business
                • Choose appropriate style for your brand
                
                **File Management:**
                • Individual files: Separate caption file for each image
                • Combined file: All captions in one organized document
                • ZIP downloads: Easy sharing and organization
                
                **Cost Optimization:**
                • Use GPT-4o-mini for cost-effective batch processing
                • Upgrade to GPT-4o for premium quality results
                • Monitor your OpenAI API usage during large batches
                """)
    
    # Footer with enhanced examples and tips
    st.markdown("---")
    st.header("💡 Success Examples & Tips")
    
    examples_tab1, examples_tab2 = st.tabs(["🎯 Example Combinations", "📚 Best Practices"])
    
    with examples_tab1:
        example_col1, example_col2, example_col3 = st.columns(3)
        
        with example_col1:
            st.info("""
            **🍝 Italian Restaurant**
            
            • **Website:** olivegarden.com
            • **Image:** Fresh pasta dish
            • **Style:** Casual & Friendly
            • **Model:** GPT-4o-mini
            • **Result:** Warm, inviting captions
            """)
        
        with example_col2:
            st.info("""
            **💪 Fitness Studio**
            
            • **Website:** orangetheory.com  
            • **Image:** Workout session
            • **Style:** Inspirational
            • **Model:** GPT-4o
            • **Result:** Motivational content
            """)
        
        with example_col3:
            st.info("""
            **☕ Coffee Shop**
            
            • **Website:** starbucks.com
            • **Image:** Latte art
            • **Style:** Professional
            • **Model:** GPT-4o-mini
            • **Result:** Brand-aligned posts
            """)
    
    with examples_tab2:
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("""
            ### 🎯 Image Best Practices
            
            ✅ **High-resolution photos** (1080x1080+ recommended)
            ✅ **Good lighting** and clear subjects  
            ✅ **Brand-relevant** content
            ✅ **People in action** for engagement
            ✅ **Behind-the-scenes** moments
            
            ❌ Avoid blurry or dark images
            ❌ Skip overly complex compositions
            ❌ Avoid copyrighted content
            """)
        
        with tips_col2:
            st.markdown("""
            ### 🚀 Caption Optimization
            
            ✅ **Hook in first sentence** to grab attention
            ✅ **Tell a story** that connects emotionally  
            ✅ **Include value** for your audience
            ✅ **End with clear CTA** when appropriate
            ✅ **Match platform** character limits
            
            ❌ Don't oversell in every post
            ❌ Avoid industry jargon
            ❌ Skip generic phrases
            """)

if __name__ == "__main__":
    main()
