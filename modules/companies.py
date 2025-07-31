#!/usr/bin/env python3
"""
Company profile management module for storing and managing business profiles.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st

from config.constants import COMPANY_DATA_FILE
from config.settings import CompanyProfile, SESSION_KEYS
from utils.file_ops import load_json_file, save_json_file
from utils.helpers import get_current_timestamp, clear_session_keys

class CompanyProfileManager:
    """Manages company profiles including CRUD operations and session management."""
    
    def __init__(self):
        self.file_path = COMPANY_DATA_FILE
    
    def load_company_profiles(self) -> Dict[str, Any]:
        """Load saved company profiles from JSON file.
        
        Company profiles are shared across all users and persist across sessions.
        
        Returns:
            Dict containing company profiles
        """
        return load_json_file(self.file_path)
    
    def save_company_profiles(self, profiles: Dict[str, Any]) -> bool:
        """Save company profiles to JSON file.
        
        Args:
            profiles: Dictionary of company profiles
            
        Returns:
            True if successful, False otherwise
        """
        return save_json_file(self.file_path, profiles)
    
    def save_company_profile(self, company_name: str, profile_data: Dict[str, Any]) -> bool:
        """Save a single company profile with timestamp tracking.
        
        Args:
            company_name: Name of the company
            profile_data: Profile data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not company_name or not profile_data:
            return False
        
        profiles = self.load_company_profiles()
        
        # Add timestamps for tracking
        profile_data.update({
            'saved_date': get_current_timestamp(),
            'last_used': get_current_timestamp()
        })
        
        profiles[company_name] = profile_data
        return self.save_company_profiles(profiles)
    
    def get_company_profile(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific company profile and update last used timestamp.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Company profile data or None if not found
        """
        if not company_name:
            return None
        
        profiles = self.load_company_profiles()
        if company_name in profiles:
            # Update last used timestamp
            profiles[company_name]['last_used'] = get_current_timestamp()
            self.save_company_profiles(profiles)
            return profiles[company_name]
        
        return None
    
    def delete_company_profile(self, company_name: str) -> bool:
        """Delete a company profile from storage.
        
        Args:
            company_name: Name of the company to delete
            
        Returns:
            True if deleted, False if not found or error
        """
        if not company_name:
            return False
        
        profiles = self.load_company_profiles()
        if company_name in profiles:
            del profiles[company_name]
            return self.save_company_profiles(profiles)
        
        return False
    
    def get_company_names(self) -> List[str]:
        """Get list of all company names.
        
        Returns:
            Sorted list of company names
        """
        profiles = self.load_company_profiles()
        return sorted(list(profiles.keys()))
    
    def company_exists(self, company_name: str) -> bool:
        """Check if a company profile exists.
        
        Args:
            company_name: Name of the company
            
        Returns:
            True if exists, False otherwise
        """
        profiles = self.load_company_profiles()
        return company_name in profiles
    
    def get_recent_companies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently used companies.
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of recent company profiles with metadata
        """
        profiles = self.load_company_profiles()
        company_list = []
        
        for name, profile in profiles.items():
            last_used = profile.get('last_used', '')
            company_list.append({
                'name': name,
                'last_used': last_used,
                'profile': profile
            })
        
        # Sort by last_used date (most recent first)
        company_list.sort(key=lambda x: x['last_used'], reverse=True)
        return company_list[:limit]
    
    def search_companies(self, search_term: str) -> List[str]:
        """Search for companies by name.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching company names
        """
        if not search_term:
            return self.get_company_names()
        
        profiles = self.load_company_profiles()
        matches = []
        
        search_lower = search_term.lower()
        for company_name in profiles:
            if search_lower in company_name.lower():
                matches.append(company_name)
        
        return sorted(matches)
    
    def create_profile_from_settings(self, settings: Dict[str, Any]) -> CompanyProfile:
        """Create a CompanyProfile object from current settings.
        
        Args:
            settings: Current session settings dictionary
            
        Returns:
            CompanyProfile object
        """
        return CompanyProfile(
            business_input=settings.get('business_input', ''),
            website_url=settings.get('website_url', ''),
            caption_style=settings.get('caption_style', 'Professional'),
            caption_length=settings.get('caption_length', 'Medium (4-6 sentences)'),
            use_premium_model=settings.get('use_premium_model', False),
            include_cta=settings.get('include_cta', True),
            focus_keywords=settings.get('focus_keywords', ''),
            avoid_words=settings.get('avoid_words', ''),
            target_audience=settings.get('target_audience', 'General'),
            text_only_mode=settings.get('text_only_mode', False),
            character_limit_preference=settings.get('character_limit_preference', 'No limit'),
            captions_generated_count=1,
            website_analysis=st.session_state.get('website_analysis')
        )
    
    def create_profile_data_from_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized profile data dictionary from current settings.
        
        Args:
            settings: Current session settings dictionary
            
        Returns:
            Standardized profile data with all required fields
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
    
    def update_company_usage(self, company_name: str) -> bool:
        """Update the last used timestamp and usage count for a company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            True if updated, False if not found or error
        """
        profiles = self.load_company_profiles()
        
        if company_name not in profiles:
            return False
        
        profile = profiles[company_name]
        profile['last_used'] = get_current_timestamp()
        profile['captions_generated_count'] = profile.get('captions_generated_count', 0) + 1
        
        profiles[company_name] = profile
        return self.save_company_profiles(profiles)
    
    def get_company_stats(self) -> Dict[str, Any]:
        """Get statistics about stored company profiles.
        
        Returns:
            Dictionary containing company statistics
        """
        profiles = self.load_company_profiles()
        
        if not profiles:
            return {
                'total_companies': 0,
                'most_recent': None,
                'most_used': None,
                'total_captions_generated': 0
            }
        
        # Calculate stats
        total_captions = 0
        most_used_company = None
        most_used_count = 0
        most_recent_company = None
        most_recent_date = None
        
        for name, profile in profiles.items():
            # Count total captions
            captions_count = profile.get('captions_generated_count', 0)
            total_captions += captions_count
            
            # Find most used
            if captions_count > most_used_count:
                most_used_count = captions_count
                most_used_company = name
            
            # Find most recent
            last_used = profile.get('last_used', '')
            if last_used and (most_recent_date is None or last_used > most_recent_date):
                most_recent_date = last_used
                most_recent_company = name
        
        return {
            'total_companies': len(profiles),
            'most_recent': most_recent_company,
            'most_used': most_used_company,
            'total_captions_generated': total_captions
        }
    
    def export_company_profiles(self) -> Optional[str]:
        """Export company profiles to CSV format.
        
        Returns:
            CSV string or None if no data
        """
        profiles = self.load_company_profiles()
        
        if not profiles:
            return None
        
        from utils.helpers import export_data_to_csv
        
        # Convert to list format for export
        data = []
        for name, profile in profiles.items():
            data.append({
                'company_name': name,
                'business_input': profile.get('business_input', ''),
                'website_url': profile.get('website_url', ''),
                'caption_style': profile.get('caption_style', ''),
                'caption_length': profile.get('caption_length', ''),
                'target_audience': profile.get('target_audience', ''),
                'saved_date': profile.get('saved_date', ''),
                'last_used': profile.get('last_used', ''),
                'captions_generated_count': profile.get('captions_generated_count', 0)
            })
        
        headers = [
            'Company Name', 'Business Input', 'Website URL', 'Caption Style', 
            'Caption Length', 'Target Audience', 'Saved Date', 'Last Used', 
            'Captions Generated Count'
        ]
        
        return export_data_to_csv(data, headers)

class SessionManager:
    """Manages session state for the application."""
    
    @staticmethod
    def clear_all_session_data() -> int:
        """Clear all session state data for starting over.
        
        Returns:
            Number of session keys cleared
        """
        # Combine all session key categories
        all_keys = []
        for key_category in SESSION_KEYS.values():
            all_keys.extend(key_category)
        
        # Also add the current_settings key
        all_keys.append('current_settings')
        
        # Clear all specified keys
        cleared_count = clear_session_keys(all_keys)
        
        # Clear cached data
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        
        return cleared_count
    
    @staticmethod
    def clear_image_data() -> int:
        """Clear only image-related session data.
        
        Returns:
            Number of session keys cleared
        """
        return clear_session_keys(SESSION_KEYS["IMAGE_KEYS"])
    
    @staticmethod
    def clear_caption_data() -> int:
        """Clear only caption-related session data.
        
        Returns:
            Number of session keys cleared
        """
        return clear_session_keys(SESSION_KEYS["CAPTION_KEYS"])
    
    @staticmethod
    def clear_ui_state() -> int:
        """Clear only UI state session data.
        
        Returns:
            Number of session keys cleared
        """
        return clear_session_keys(SESSION_KEYS["UI_KEYS"])

# Convenience functions for backward compatibility and easy access
def get_company_manager() -> CompanyProfileManager:
    """Get a CompanyProfileManager instance.
    
    Returns:
        CompanyProfileManager instance
    """
    return CompanyProfileManager()

def get_session_manager() -> SessionManager:
    """Get a SessionManager instance.
    
    Returns:
        SessionManager instance
    """
    return SessionManager()

# Legacy function wrappers for backward compatibility
def load_company_profiles() -> Dict[str, Any]:
    """Legacy wrapper for loading company profiles."""
    return get_company_manager().load_company_profiles()

def save_company_profiles(profiles: Dict[str, Any]) -> bool:
    """Legacy wrapper for saving company profiles."""
    return get_company_manager().save_company_profiles(profiles)

def save_company_profile(company_name: str, profile_data: Dict[str, Any]) -> bool:
    """Legacy wrapper for saving a company profile."""
    return get_company_manager().save_company_profile(company_name, profile_data)

def get_company_profile(company_name: str) -> Optional[Dict[str, Any]]:
    """Legacy wrapper for getting a company profile."""
    return get_company_manager().get_company_profile(company_name)

def delete_company_profile(company_name: str) -> bool:
    """Legacy wrapper for deleting a company profile."""
    return get_company_manager().delete_company_profile(company_name)

def create_profile_data_from_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy wrapper for creating profile data from settings."""
    return get_company_manager().create_profile_data_from_settings(settings)

def clear_all_session_data() -> int:
    """Legacy wrapper for clearing all session data."""
    return get_session_manager().clear_all_session_data()
