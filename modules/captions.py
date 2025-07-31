#!/usr/bin/env python3
"""
Caption management module for tracking and managing used captions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from config.constants import USED_CAPTIONS_FILE
from utils.file_ops import load_json_file, save_json_file
from utils.helpers import (
    create_hash, 
    calculate_similarity, 
    is_recent_date, 
    get_current_timestamp,
    export_data_to_csv
)

class CaptionManager:
    """Manages caption tracking, duplicate detection, and usage statistics."""
    
    def __init__(self):
        self.file_path = USED_CAPTIONS_FILE
    
    def load_used_captions(self) -> Dict[str, Any]:
        """Load used captions from JSON file.
        
        Returns:
            Dict containing used captions data
        """
        return load_json_file(self.file_path)
    
    def save_used_captions(self, used_captions: Dict[str, Any]) -> bool:
        """Save used captions to JSON file.
        
        Args:
            used_captions: Dictionary of used captions data
            
        Returns:
            True if successful, False otherwise
        """
        return save_json_file(self.file_path, used_captions)
    
    def mark_caption_as_used(self, caption_text: str, business_name: str = "") -> bool:
        """Mark a caption as used.
        
        Args:
            caption_text: The caption text to mark as used
            business_name: Associated business name
            
        Returns:
            True if successful, False otherwise
        """
        if not caption_text.strip():
            return False
        
        caption_hash = create_hash(caption_text)
        used_captions = self.load_used_captions()
        timestamp = get_current_timestamp()
        
        used_captions[caption_hash] = {
            'text': caption_text.strip(),
            'business': business_name,
            'used_date': timestamp,
            'usage_count': used_captions.get(caption_hash, {}).get('usage_count', 0) + 1
        }
        
        return self.save_used_captions(used_captions)
    
    def unmark_caption_as_used(self, caption_text: str) -> bool:
        """Remove a caption from the used captions history.
        
        Args:
            caption_text: The caption text to remove
            
        Returns:
            True if removed, False if not found or error
        """
        if not caption_text.strip():
            return False
        
        caption_hash = create_hash(caption_text)
        used_captions = self.load_used_captions()
        
        if caption_hash in used_captions:
            del used_captions[caption_hash]
            return self.save_used_captions(used_captions)
        
        return False
    
    def is_caption_duplicate(self, caption_text: str, threshold: float = 0.8) -> Tuple[bool, Optional[Dict]]:
        """Check if a caption is too similar to previously used captions.
        
        Args:
            caption_text: Caption text to check
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (is_duplicate, duplicate_data)
        """
        if not caption_text.strip():
            return False, None
        
        caption_hash = create_hash(caption_text)
        used_captions = self.load_used_captions()
        
        # Exact match
        if caption_hash in used_captions:
            return True, used_captions[caption_hash]
        
        # Similarity check
        for stored_hash, stored_data in used_captions.items():
            stored_text = stored_data.get('text', '')
            similarity = calculate_similarity(caption_text, stored_text)
            
            if similarity >= threshold:
                return True, stored_data
        
        return False, None
    
    def get_caption_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about caption usage.
        
        Returns:
            Dictionary containing usage statistics
        """
        used_captions = self.load_used_captions()
        
        stats = {
            'total_used': len(used_captions),
            'recent_used': 0,
            'most_used_business': 'N/A',
            'total_usage_count': 0,
            'avg_usage_per_caption': 0.0
        }
        
        if not used_captions:
            return stats
        
        recent_count = 0
        business_counts = {}
        total_usage = 0
        
        for caption_data in used_captions.values():
            usage_count = caption_data.get('usage_count', 1)
            total_usage += usage_count
            
            # Check if recent (last 7 days)
            used_date = caption_data.get('used_date', '')
            if is_recent_date(used_date, days=7):
                recent_count += 1
            
            # Count by business
            business = caption_data.get('business', 'Unknown')
            business_counts[business] = business_counts.get(business, 0) + 1
        
        stats.update({
            'recent_used': recent_count,
            'total_usage_count': total_usage,
            'avg_usage_per_caption': round(total_usage / len(used_captions), 2)
        })
        
        if business_counts:
            stats['most_used_business'] = max(business_counts, key=business_counts.get)
        
        return stats
    
    def search_used_captions(self, search_query: str = "", business_filter: str = "", 
                           date_filter: str = "") -> List[Dict[str, Any]]:
        """Search used captions with filters.
        
        Args:
            search_query: Text to search for in captions
            business_filter: Business name to filter by
            date_filter: Date to filter by (ISO format)
            
        Returns:
            List of matching caption records
        """
        used_captions = self.load_used_captions()
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
                except (ValueError, TypeError):
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
    
    def get_unique_businesses(self) -> List[str]:
        """Get list of unique businesses from used captions.
        
        Returns:
            Sorted list of unique business names
        """
        used_captions = self.load_used_captions()
        businesses = set()
        
        for caption_data in used_captions.values():
            business = caption_data.get('business', '').strip()
            if business:
                businesses.add(business)
        
        return sorted(list(businesses))
    
    def delete_multiple_captions(self, caption_hashes: List[str]) -> int:
        """Delete multiple captions from usage history.
        
        Args:
            caption_hashes: List of caption hashes to delete
            
        Returns:
            Number of captions deleted
        """
        if not caption_hashes:
            return 0
            
        used_captions = self.load_used_captions()
        deleted_count = 0
        
        for caption_hash in caption_hashes:
            if caption_hash in used_captions:
                del used_captions[caption_hash]
                deleted_count += 1
        
        if deleted_count > 0:
            self.save_used_captions(used_captions)
        
        return deleted_count
    
    def export_caption_history(self) -> Optional[str]:
        """Export caption history to CSV format.
        
        Returns:
            CSV string or None if no data
        """
        used_captions = self.load_used_captions()
        
        if not used_captions:
            return None
        
        # Convert to list format for export
        data = []
        for caption_data in used_captions.values():
            data.append({
                'caption_text': caption_data.get('text', ''),
                'business': caption_data.get('business', ''),
                'used_date': caption_data.get('used_date', ''),
                'usage_count': caption_data.get('usage_count', 1)
            })
        
        headers = ['Caption Text', 'Business', 'Used Date', 'Usage Count']
        return export_data_to_csv(data, headers)
    
    def get_recent_captions(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently used captions.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of captions to return
            
        Returns:
            List of recent caption records
        """
        used_captions = self.load_used_captions()
        recent_captions = []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for caption_hash, caption_data in used_captions.items():
            used_date = caption_data.get('used_date', '')
            try:
                caption_date = datetime.fromisoformat(used_date)
                if caption_date >= cutoff_date:
                    recent_captions.append({
                        'hash': caption_hash,
                        'text': caption_data.get('text', ''),
                        'business': caption_data.get('business', ''),
                        'used_date': used_date,
                        'usage_count': caption_data.get('usage_count', 1)
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by most recent first and limit results
        recent_captions.sort(key=lambda x: x['used_date'], reverse=True)
        return recent_captions[:limit]
    
    def bulk_import_captions(self, captions: List[Dict[str, Any]]) -> int:
        """Bulk import captions from a list.
        
        Args:
            captions: List of caption dictionaries with 'text' and 'business' keys
            
        Returns:
            Number of captions imported
        """
        if not captions:
            return 0
        
        imported_count = 0
        for caption_data in captions:
            caption_text = caption_data.get('text', '').strip()
            business_name = caption_data.get('business', '')
            
            if caption_text:
                if self.mark_caption_as_used(caption_text, business_name):
                    imported_count += 1
        
        return imported_count

# Convenience functions for backward compatibility and easy access
def get_caption_manager() -> CaptionManager:
    """Get a CaptionManager instance.
    
    Returns:
        CaptionManager instance
    """
    return CaptionManager()

# Legacy function wrappers for backward compatibility
def load_used_captions() -> Dict[str, Any]:
    """Legacy wrapper for loading used captions."""
    return get_caption_manager().load_used_captions()

def save_used_captions(used_captions: Dict[str, Any]) -> bool:
    """Legacy wrapper for saving used captions."""
    return get_caption_manager().save_used_captions(used_captions)

def mark_caption_as_used(caption_text: str, business_name: str = "") -> bool:
    """Legacy wrapper for marking caption as used."""
    return get_caption_manager().mark_caption_as_used(caption_text, business_name)

def unmark_caption_as_used(caption_text: str) -> bool:
    """Legacy wrapper for unmarking caption as used."""
    return get_caption_manager().unmark_caption_as_used(caption_text)

def is_caption_duplicate(caption_text: str, threshold: float = 0.8) -> Tuple[bool, Optional[Dict]]:
    """Legacy wrapper for checking caption duplicates."""
    return get_caption_manager().is_caption_duplicate(caption_text, threshold)

def get_caption_usage_stats() -> Dict[str, Any]:
    """Legacy wrapper for getting caption usage stats."""
    return get_caption_manager().get_caption_usage_stats()

def search_used_captions(search_query: str = "", business_filter: str = "", 
                        date_filter: str = "") -> List[Dict[str, Any]]:
    """Legacy wrapper for searching used captions."""
    return get_caption_manager().search_used_captions(search_query, business_filter, date_filter)

def get_unique_businesses() -> List[str]:
    """Legacy wrapper for getting unique businesses."""
    return get_caption_manager().get_unique_businesses()

def delete_multiple_captions(caption_hashes: List[str]) -> int:
    """Legacy wrapper for deleting multiple captions."""
    return get_caption_manager().delete_multiple_captions(caption_hashes)

def export_caption_history() -> Optional[str]:
    """Legacy wrapper for exporting caption history."""
    return get_caption_manager().export_caption_history()
