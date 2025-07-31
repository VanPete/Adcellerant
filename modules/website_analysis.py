#!/usr/bin/env python3
"""
Website analysis module for extracting business information from websites.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any, Tuple

from config.constants import REQUEST_TIMEOUT, MAX_RETRIES, WEBSITE_ANALYSIS_TTL
from utils.helpers import validate_url, clean_text, truncate_text

class WebsiteAnalyzer:
    """Analyzes websites to extract business information and images."""
    
    def __init__(self):
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.headers_list = [
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
    
    @st.cache_data(ttl=WEBSITE_ANALYSIS_TTL, show_spinner=False)
    def analyze_website(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract key information from a company's website including multiple pages.
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Dictionary containing website analysis or None if failed
        """
        if not url:
            return None
        
        try:
            # Normalize URL
            url = validate_url(url)
            base_domain = urlparse(url).netloc
            
            # Fetch main page
            main_response = self._fetch_page_with_retries(url)
            if not main_response:
                raise Exception("Failed to fetch main page after trying multiple approaches")
            
            main_soup = BeautifulSoup(main_response.content, 'html.parser')
            
            # Get priority pages to analyze
            priority_pages = self._discover_priority_pages(url, base_domain, main_soup)
            
            # Initialize analysis structure
            analysis = self._initialize_analysis(main_soup, url)
            
            # Fetch and analyze all pages
            all_soups = [main_soup]
            for page_url in priority_pages:
                try:
                    page_response = self._fetch_page_with_retries(page_url)
                    if page_response:
                        page_soup = BeautifulSoup(page_response.content, 'html.parser')
                        all_soups.append(page_soup)
                        analysis['pages_analyzed'].append(page_url)
                except Exception:
                    continue
            
            # Extract and process content from all pages
            analysis.update(self._extract_content_from_pages(all_soups))
            
            # Extract images from main page
            analysis['images'] = self.extract_website_images(url, main_soup)
            
            return analysis
            
        except Exception as e:
            self._handle_website_analysis_error(e, url)
            return None
    
    def _fetch_page_with_retries(self, page_url: str) -> Optional[requests.Response]:
        """Fetch a page with multiple user agent retries.
        
        Args:
            page_url: URL to fetch
            
        Returns:
            Response object or None if failed
        """
        for headers in self.headers_list:
            try:
                response = requests.get(
                    page_url, 
                    headers=headers, 
                    timeout=self.timeout, 
                    allow_redirects=True
                )
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
    
    def _discover_priority_pages(self, url: str, base_domain: str, main_soup: BeautifulSoup) -> List[str]:
        """Discover and score priority pages for analysis.
        
        Args:
            url: Base URL
            base_domain: Domain name
            main_soup: BeautifulSoup object of main page
            
        Returns:
            List of priority page URLs
        """
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
        
        for link in links[:150]:  # Limit to first 150 links for performance
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
            skip_patterns = [
                '#', 'mailto:', 'tel:', 'javascript:', '.pdf', '.jpg', '.png', '.gif', 
                '.doc', '.docx', '.zip', '.csv', 'login', 'register', 'cart', 'checkout',
                'privacy', 'terms', 'cookie', 'sitemap.xml', '.xml', 'feed', 'rss'
            ]
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
    
    def _initialize_analysis(self, main_soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Initialize the analysis structure with main page data.
        
        Args:
            main_soup: BeautifulSoup object of main page
            url: URL being analyzed
            
        Returns:
            Initial analysis dictionary
        """
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
    
    def _extract_content_from_pages(self, all_soups: List[BeautifulSoup]) -> Dict[str, Any]:
        """Extract and process content from all analyzed pages.
        
        Args:
            all_soups: List of BeautifulSoup objects
            
        Returns:
            Dictionary with extracted content
        """
        all_about_text = []
        all_services = []
        
        for soup in all_soups:
            # Extract about text
            about_sections = soup.find_all(
                ['div', 'section', 'p', 'h1', 'h2', 'h3', 'article'], 
                class_=lambda x: x and any(
                    word in x.lower() for word in [
                        'about', 'mission', 'vision', 'story', 'who-we-are', 
                        'company', 'intro', 'overview'
                    ]
                )
            )
            
            # Also check by ID
            about_sections.extend(
                soup.find_all(
                    ['div', 'section'], 
                    id=lambda x: x and any(
                        word in x.lower() for word in ['about', 'mission', 'vision', 'story', 'company']
                    )
                )
            )
            
            # Main content areas
            main_content = soup.find_all(['main', 'article', '.content', '.main-content'])
            if main_content:
                about_sections.extend(main_content)
            
            # Process about text
            page_about_text = []
            for section in about_sections[:8]:
                text = section.get_text(strip=True)
                if len(text) > 50 and not any(
                    skip in text.lower() for skip in ['cookie', 'privacy', 'terms', 'menu', 'navigation']
                ):
                    page_about_text.append(text)
            
            combined_text = ' '.join(page_about_text)
            if combined_text and len(combined_text) > 30:
                all_about_text.append(combined_text)
            
            # Extract services
            service_sections = soup.find_all(
                ['div', 'section', 'li', 'h2', 'h3', 'h4', 'article'], 
                class_=lambda x: x and any(
                    word in x.lower() for word in [
                        'service', 'product', 'offering', 'solution', 'feature', 'specialty', 'expertise'
                    ]
                )
            )
            
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
            'about_text': self._process_about_text(all_about_text),
            'services': self._process_services(all_services)
        }
    
    def _process_about_text(self, all_about_text: List[str]) -> str:
        """Process and deduplicate about text.
        
        Args:
            all_about_text: List of about text strings
            
        Returns:
            Processed and deduplicated about text
        """
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
        
        return truncate_text(' '.join(unique_about_texts), 1200)
    
    def _process_services(self, all_services: List[str]) -> List[str]:
        """Process and deduplicate services.
        
        Args:
            all_services: List of service strings
            
        Returns:
            Processed and deduplicated services list
        """
        clean_services = []
        for service in all_services:
            if not any(
                skip in service.lower() for skip in [
                    'read more', 'learn more', 'contact', 'click here', 'view all'
                ]
            ):
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
    
    def _handle_website_analysis_error(self, error: Exception, url: str):
        """Handle and display appropriate error messages for website analysis failures.
        
        Args:
            error: The exception that occurred
            url: URL that failed to analyze
        """
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
    
    @st.cache_data(ttl=WEBSITE_ANALYSIS_TTL)
    def extract_website_images(self, base_url: str, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract relevant images from website for potential social media use.
        
        Args:
            base_url: Base URL of the website
            soup: BeautifulSoup object of the page
            
        Returns:
            List of image dictionaries with metadata
        """
        if not base_url or not soup:
            return []
            
        try:
            images = []
            img_tags = soup.find_all('img')
            
            # Process up to 10 images to avoid excessive processing
            for img in img_tags[:10]:
                processed_image = self._process_image_tag(img, base_url)
                if processed_image:
                    images.append(processed_image)
            
            return images[:5]  # Return top 5 suitable images
            
        except Exception as e:
            st.warning(f"⚠️ Error extracting website images: {str(e)}")
            return []
    
    def _process_image_tag(self, img, base_url: str) -> Optional[Dict[str, str]]:
        """Process a single image tag and return image info if suitable.
        
        Args:
            img: BeautifulSoup img tag
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Dictionary with image metadata or None if unsuitable
        """
        # Get image source
        src = img.get('src') or img.get('data-src')
        if not src:
            return None
        
        # Convert to absolute URL
        src = self._normalize_image_url(src, base_url)
        if not src:
            return None
        
        # Filter out unwanted images
        if self._should_skip_image(src):
            return None
        
        # Check image dimensions
        if not self._has_suitable_dimensions(img):
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
    
    def _normalize_image_url(self, src: str, base_url: str) -> str:
        """Normalize image URL to absolute format.
        
        Args:
            src: Image source URL
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Normalized absolute URL
        """
        if src.startswith('//'):
            return 'https:' + src
        elif src.startswith('/'):
            return urljoin(base_url, src)
        elif not src.startswith(('http://', 'https://')):
            return urljoin(base_url, src)
        return src
    
    def _should_skip_image(self, src: str) -> bool:
        """Check if image should be skipped based on URL patterns.
        
        Args:
            src: Image source URL
            
        Returns:
            True if image should be skipped
        """
        skip_patterns = ['logo', 'icon', 'favicon', 'avatar', 'thumb', 'badge', 'button']
        return any(skip in src.lower() for skip in skip_patterns)
    
    def _has_suitable_dimensions(self, img) -> bool:
        """Check if image has suitable dimensions for social media.
        
        Args:
            img: BeautifulSoup img tag
            
        Returns:
            True if dimensions are suitable
        """
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
    
    def analyze_website_with_spinner(self, url: str) -> Optional[Dict[str, Any]]:
        """Wrapper function to show spinner while analyzing website.
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Website analysis dictionary or None
        """
        with st.spinner(f"🌐 Analyzing website: {url}"):
            return self.analyze_website(url)

# Convenience functions for backward compatibility and easy access
def get_website_analyzer() -> WebsiteAnalyzer:
    """Get a WebsiteAnalyzer instance.
    
    Returns:
        WebsiteAnalyzer instance
    """
    return WebsiteAnalyzer()

# Legacy function wrappers for backward compatibility
def analyze_website(url: str) -> Optional[Dict[str, Any]]:
    """Legacy wrapper for website analysis."""
    return get_website_analyzer().analyze_website(url)

def extract_website_images(base_url: str, soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Legacy wrapper for image extraction."""
    return get_website_analyzer().extract_website_images(base_url, soup)

def analyze_website_with_spinner(url: str) -> Optional[Dict[str, Any]]:
    """Legacy wrapper for website analysis with spinner."""
    return get_website_analyzer().analyze_website_with_spinner(url)
