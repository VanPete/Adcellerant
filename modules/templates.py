#!/usr/bin/env python3
"""
Templates and analytics module for social media post templates and user feedback tracking.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st

from config.constants import FEEDBACK_FILE, STATS_FILE
from utils.file_ops import load_json_file, save_json_file

class TemplateManager:
    """Manages social media post templates and platform specifications."""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.platform_specs = self._load_platform_specs()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load predefined templates for different social media platforms and post types."""
        return {
            "Instagram": {
                "Product Showcase": {
                    "prompt_template": "Create an engaging Instagram post for {business} showcasing {product_name}. Include relevant hashtags, call-to-action, and trendy language. Focus on visual appeal and lifestyle benefits.",
                    "hashtag_suggestions": ["#product", "#lifestyle", "#quality", "#style", "#trending"],
                    "cta_examples": ["Shop now!", "Link in bio!", "DM for details!", "Swipe up!"],
                    "best_practices": ["Use 3-5 hashtags", "Include call-to-action", "Ask questions to boost engagement", "Tag relevant accounts"]
                },
                "Behind the Scenes": {
                    "prompt_template": "Create a behind-the-scenes Instagram post for {business}. Show the process, team, or workspace. Make it authentic and relatable with appropriate hashtags.",
                    "hashtag_suggestions": ["#behindthescenes", "#process", "#team", "#authentic", "#workspace"],
                    "cta_examples": ["What do you think?", "Any questions?", "Follow for more!", "Share your thoughts!"],
                    "best_practices": ["Be authentic", "Show personality", "Include team members", "Explain your process"]
                },
                "Quote/Motivation": {
                    "prompt_template": "Create an inspirational Instagram post for {business} with a motivational quote or message. Include relevant industry wisdom and encouraging hashtags.",
                    "hashtag_suggestions": ["#motivation", "#inspiration", "#success", "#mindset", "#goals"],
                    "cta_examples": ["What motivates you?", "Share this with someone!", "Tag a friend!", "Double tap if you agree!"],
                    "best_practices": ["Use inspiring imagery", "Keep text readable", "Make it shareable", "Connect to your brand values"]
                },
                "Story/Carousel": {
                    "prompt_template": "Create an Instagram carousel/story post for {business}. Include multiple slides worth of content with tips, steps, or educational content.",
                    "hashtag_suggestions": ["#tips", "#education", "#howto", "#carousel", "#learn"],
                    "cta_examples": ["Swipe for more!", "Save this post!", "Try this at home!", "Which tip is your favorite?"],
                    "best_practices": ["Create visual consistency", "Number your slides", "Include a summary slide", "Encourage saves"]
                }
            },
            "Facebook": {
                "Business Update": {
                    "prompt_template": "Create a Facebook business update for {business}. Share news, achievements, or changes in a professional yet friendly tone. Include community engagement elements.",
                    "hashtag_suggestions": ["#businessupdate", "#news", "#community", "#achievement"],
                    "cta_examples": ["Learn more on our website", "Contact us for details", "What are your thoughts?", "Share with friends!"],
                    "best_practices": ["Longer form content works", "Include links", "Encourage comments", "Share personal stories"]
                },
                "Event Promotion": {
                    "prompt_template": "Create a Facebook event promotion post for {business}. Include event details, benefits of attending, and create excitement. Add clear next steps.",
                    "hashtag_suggestions": ["#event", "#join", "#community", "#networking", "#learning"],
                    "cta_examples": ["Register now!", "See you there!", "Mark your calendar!", "Invite your friends!"],
                    "best_practices": ["Include event details", "Create urgency", "Show social proof", "Make registration easy"]
                },
                "Educational/Tips": {
                    "prompt_template": "Create an educational Facebook post for {business}. Share valuable tips, insights, or how-to content that helps your audience. Make it informative and actionable.",
                    "hashtag_suggestions": ["#tips", "#education", "#howto", "#advice", "#helpful"],
                    "cta_examples": ["Try this tip!", "What's your experience?", "Share your own tips!", "Bookmark for later!"],
                    "best_practices": ["Provide real value", "Use numbered lists", "Include examples", "Encourage discussion"]
                }
            },
            "LinkedIn": {
                "Professional Insight": {
                    "prompt_template": "Create a professional LinkedIn post for {business}. Share industry insights, thought leadership, or professional experience. Maintain authoritative and networking-friendly tone.",
                    "hashtag_suggestions": ["#professional", "#industry", "#leadership", "#networking", "#business"],
                    "cta_examples": ["What's your take?", "Connect with me!", "Interested in learning more?", "Let's discuss in comments!"],
                    "best_practices": ["Professional tone", "Share expertise", "Ask thoughtful questions", "Network actively"]
                },
                "Company Achievement": {
                    "prompt_template": "Create a LinkedIn company achievement post for {business}. Celebrate milestones, awards, team success, or growth in a professional manner.",
                    "hashtag_suggestions": ["#achievement", "#milestone", "#team", "#success", "#growth"],
                    "cta_examples": ["Proud of our team!", "Thank you for your support!", "Onward and upward!", "Grateful for this recognition!"],
                    "best_practices": ["Credit team members", "Show gratitude", "Include metrics", "Tag relevant people"]
                },
                "Industry News": {
                    "prompt_template": "Create a LinkedIn industry news commentary for {business}. Share thoughts on recent industry developments, trends, or news with professional analysis.",
                    "hashtag_suggestions": ["#industryNEWS", "#trends", "#analysis", "#future", "#innovation"],
                    "cta_examples": ["What are your thoughts?", "How do you see this impacting us?", "Interested in discussing?", "What's your prediction?"],
                    "best_practices": ["Add your perspective", "Cite sources", "Encourage professional discussion", "Show expertise"]
                }
            },
            "Twitter": {
                "Quick Update": {
                    "prompt_template": "Create a concise Twitter update for {business}. Keep it under 280 characters, include relevant hashtags, and make it engaging for retweets.",
                    "hashtag_suggestions": ["#update", "#news", "#quick", "#twitter"],
                    "cta_examples": ["RT if you agree!", "Thoughts?", "What do you think?", "Share your experience!"],
                    "best_practices": ["Stay under 280 characters", "Use trending hashtags", "Include multimedia", "Time posts well"]
                },
                "Engagement/Poll": {
                    "prompt_template": "Create a Twitter engagement post or poll question for {business}. Make it interactive, fun, and relevant to your audience.",
                    "hashtag_suggestions": ["#poll", "#question", "#engage", "#community"],
                    "cta_examples": ["Vote below!", "RT with your answer!", "What's your choice?", "This or that?"],
                    "best_practices": ["Ask simple questions", "Use Twitter polls", "Create controversy (respectfully)", "Reply to responses"]
                }
            },
            "TikTok": {
                "Trend Participation": {
                    "prompt_template": "Create a TikTok trend participation post for {business}. Adapt current trends to your brand, use trending sounds, and keep it fun and authentic.",
                    "hashtag_suggestions": ["#trending", "#fyp", "#viral", "#fun", "#authentic"],
                    "cta_examples": ["Try this trend!", "Duet with us!", "Share your version!", "Follow for more!"],
                    "best_practices": ["Follow current trends", "Use trending sounds", "Keep it short and snappy", "Be authentic"]
                },
                "Educational/Quick Tips": {
                    "prompt_template": "Create a quick educational TikTok for {business}. Share fast tips, hacks, or behind-the-scenes knowledge in an entertaining way.",
                    "hashtag_suggestions": ["#tips", "#hacks", "#learn", "#education", "#quicktips"],
                    "cta_examples": ["Save this tip!", "Try it out!", "Follow for more tips!", "Which tip worked for you?"],
                    "best_practices": ["Keep it under 60 seconds", "Use text overlays", "Fast-paced editing", "Include a hook"]
                }
            }
        }
    
    def _load_platform_specs(self) -> Dict[str, Any]:
        """Load technical specifications for different social media platforms."""
        return {
            "Instagram": {
                "image_sizes": {
                    "Square Post": "1080×1080px",
                    "Portrait Post": "1080×1350px", 
                    "Landscape Post": "1080×566px",
                    "Story": "1080×1920px",
                    "Reels": "1080×1920px"
                },
                "caption_limits": {
                    "Post": "2,200 characters",
                    "Story": "No character limit",
                    "Bio": "150 characters"
                },
                "hashtag_limits": {
                    "Posts": "30 hashtags max",
                    "Stories": "10 hashtags max",
                    "Recommended": "3-5 hashtags"
                },
                "best_posting_times": ["11 AM - 1 PM", "7 PM - 9 PM"],
                "engagement_tips": ["Use Stories polls", "Ask questions", "Share user content", "Post consistently"]
            },
            "Facebook": {
                "image_sizes": {
                    "Post Image": "1200×630px",
                    "Cover Photo": "1640×856px",
                    "Profile Picture": "170×170px",
                    "Event Cover": "1920×1080px"
                },
                "caption_limits": {
                    "Post": "63,206 characters",
                    "Bio": "101 characters"
                },
                "best_posting_times": ["1 PM - 3 PM", "6 PM - 9 PM"],
                "engagement_tips": ["Post longer content", "Use Facebook Live", "Create events", "Share links"]
            },
            "LinkedIn": {
                "image_sizes": {
                    "Post Image": "1200×627px",
                    "Cover Photo": "1584×396px",
                    "Profile Picture": "400×400px",
                    "Company Logo": "300×300px"
                },
                "caption_limits": {
                    "Post": "3,000 characters",
                    "Headline": "120 characters",
                    "Summary": "2,000 characters"
                },
                "best_posting_times": ["8 AM - 10 AM", "12 PM - 2 PM", "5 PM - 6 PM"],
                "engagement_tips": ["Share industry insights", "Network actively", "Post during business hours", "Use professional tone"]
            },
            "Twitter": {
                "image_sizes": {
                    "Tweet Image": "1200×675px",
                    "Header": "1500×500px",
                    "Profile Picture": "400×400px"
                },
                "caption_limits": {
                    "Tweet": "280 characters",
                    "Bio": "160 characters"
                },
                "best_posting_times": ["9 AM - 10 AM", "12 PM - 1 PM", "7 PM - 9 PM"],
                "engagement_tips": ["Use trending hashtags", "Retweet and reply", "Join conversations", "Post frequently"]
            },
            "TikTok": {
                "video_specs": {
                    "Aspect Ratio": "9:16 (vertical)",
                    "Resolution": "1080×1920px",
                    "Duration": "15 seconds - 10 minutes",
                    "File Size": "Up to 500MB"
                },
                "caption_limits": {
                    "Caption": "2,200 characters",
                    "Bio": "80 characters"
                },
                "best_posting_times": ["6 AM - 10 AM", "7 PM - 9 PM"],
                "engagement_tips": ["Follow trends", "Use trending sounds", "Post consistently", "Engage with comments"]
            }
        }
    
    def get_templates(self) -> Dict[str, Any]:
        """Get all available templates."""
        return self.templates
    
    def get_platform_templates(self, platform: str) -> Dict[str, Any]:
        """Get templates for a specific platform."""
        return self.templates.get(platform, {})
    
    def get_template(self, platform: str, template_type: str) -> Optional[Dict[str, Any]]:
        """Get a specific template."""
        return self.templates.get(platform, {}).get(template_type, None)
    
    def get_platform_specs(self) -> Dict[str, Any]:
        """Get all platform specifications."""
        return self.platform_specs
    
    def get_platform_spec(self, platform: str) -> Dict[str, Any]:
        """Get specifications for a specific platform."""
        return self.platform_specs.get(platform, {})
    
    def apply_template(self, platform: str, template_type: str, business_name: str, 
                      additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply template with business-specific information.
        
        Args:
            platform: Social media platform name
            template_type: Type of template to use
            business_name: Name of the business
            additional_params: Additional parameters for template formatting
            
        Returns:
            Dictionary containing formatted template information
        """
        template_data = self.get_template(platform, template_type)
        if not template_data:
            return {
                'prompt': f"Create a {platform} post for {business_name}.",
                'hashtags': [],
                'cta_examples': [],
                'best_practices': []
            }
        
        if not additional_params:
            additional_params = {}
        
        # Add business name to parameters
        params = {'business': business_name}
        params.update(additional_params)
        
        # Format the template
        try:
            formatted_prompt = template_data['prompt_template'].format(**params)
            return {
                'prompt': formatted_prompt,
                'hashtags': template_data.get('hashtag_suggestions', []),
                'cta_examples': template_data.get('cta_examples', []),
                'best_practices': template_data.get('best_practices', [])
            }
        except KeyError as e:
            # Handle missing parameters gracefully
            return {
                'prompt': f"Create a {platform} {template_type.lower()} post for {business_name}. " + template_data['prompt_template'],
                'hashtags': template_data.get('hashtag_suggestions', []),
                'cta_examples': template_data.get('cta_examples', []),
                'best_practices': template_data.get('best_practices', [])
            }
    
    def get_platform_list(self) -> List[str]:
        """Get list of available platforms."""
        return list(self.templates.keys())
    
    def get_template_types(self, platform: str) -> List[str]:
        """Get list of available template types for a platform."""
        return list(self.templates.get(platform, {}).keys())

class FeedbackManager:
    """Manages user feedback submissions and analysis."""
    
    def __init__(self):
        pass
    
    def load_submissions(self) -> List[Dict[str, Any]]:
        """Load feedback submissions from JSON file."""
        return load_json_file(FEEDBACK_FILE, default=[])
    
    def save_submission(self, feedback_data: Dict[str, Any]) -> bool:
        """Save feedback submission to JSON file.
        
        Args:
            feedback_data: Dictionary containing feedback information
            
        Returns:
            Boolean indicating success
        """
        try:
            feedback_list = self.load_submissions()
            
            # Add timestamp and ID
            feedback_data.update({
                'submission_date': datetime.now().isoformat(),
                'id': len(feedback_list) + 1
            })
            
            feedback_list.append(feedback_data)
            return save_json_file(FEEDBACK_FILE, feedback_list)
            
        except Exception as e:
            st.error(f"Error saving feedback: {str(e)}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of feedback submissions.
        
        Returns:
            Dictionary containing feedback statistics
        """
        feedback_list = self.load_submissions()
        
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
    
    def export_data(self) -> str:
        """Export feedback data to CSV format.
        
        Returns:
            CSV formatted string
        """
        feedback_list = self.load_submissions()
        
        if not feedback_list:
            return "No feedback data available."
        
        import csv
        import io
        
        output = io.StringIO()
        fieldnames = ['id', 'type', 'title', 'description', 'rating', 'submission_date']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for feedback in feedback_list:
            writer.writerow({
                'id': feedback.get('id', ''),
                'type': feedback.get('type', ''),
                'title': feedback.get('title', ''),
                'description': feedback.get('description', ''),
                'rating': feedback.get('rating', ''),
                'submission_date': feedback.get('submission_date', '')
            })
        
        return output.getvalue()

class StatisticsManager:
    """Manages application usage statistics."""
    
    def __init__(self):
        pass
    
    def load_statistics(self) -> Dict[str, Any]:
        """Load app statistics from JSON file."""
        default_stats = {
            'total_captions_generated': 0,
            'total_sessions': 0,
            'first_use_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        return load_json_file(STATS_FILE, default=default_stats)
    
    def save_statistics(self, stats: Dict[str, Any]) -> bool:
        """Save app statistics to JSON file.
        
        Args:
            stats: Dictionary containing statistics
            
        Returns:
            Boolean indicating success
        """
        stats['last_updated'] = datetime.now().isoformat()
        return save_json_file(STATS_FILE, stats)
    
    def increment_captions_generated(self, count: int = 3) -> int:
        """Increment the total captions generated counter.
        
        Args:
            count: Number of captions to add
            
        Returns:
            New total count
        """
        stats = self.load_statistics()
        stats['total_captions_generated'] += count
        self.save_statistics(stats)
        return stats['total_captions_generated']
    
    def increment_sessions(self) -> int:
        """Increment the total sessions counter.
        
        Returns:
            New total session count
        """
        stats = self.load_statistics()
        stats['total_sessions'] += 1
        self.save_statistics(stats)
        return stats['total_sessions']
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of application usage.
        
        Returns:
            Dictionary containing usage statistics
        """
        stats = self.load_statistics()
        
        try:
            first_use = datetime.fromisoformat(stats['first_use_date'])
            days_since_first_use = (datetime.now() - first_use).days
        except:
            days_since_first_use = 0
        
        try:
            last_updated = datetime.fromisoformat(stats['last_updated'])
            days_since_last_use = (datetime.now() - last_updated).days
        except:
            days_since_last_use = 0
        
        return {
            'total_captions': stats['total_captions_generated'],
            'total_sessions': stats['total_sessions'],
            'days_since_first_use': days_since_first_use,
            'days_since_last_use': days_since_last_use,
            'avg_captions_per_session': stats['total_captions_generated'] / max(stats['total_sessions'], 1),
            'first_use_date': stats['first_use_date'],
            'last_updated': stats['last_updated']
        }

# Convenience functions for easy access
def get_template_manager() -> TemplateManager:
    """Get a TemplateManager instance."""
    return TemplateManager()

def get_feedback_manager() -> FeedbackManager:
    """Get a FeedbackManager instance."""
    return FeedbackManager()

def get_statistics_manager() -> StatisticsManager:
    """Get a StatisticsManager instance."""
    return StatisticsManager()

# Legacy function wrappers for backward compatibility
def get_post_templates() -> Dict[str, Any]:
    """Legacy wrapper for getting post templates."""
    return get_template_manager().get_templates()

def get_platform_specs() -> Dict[str, Any]:
    """Legacy wrapper for getting platform specifications."""
    return get_template_manager().get_platform_specs()

def apply_template(template_data: Dict[str, Any], business_name: str, 
                  additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Legacy wrapper for applying templates."""
    if not additional_params:
        additional_params = {}
    
    # Add business name to parameters
    params = {'business': business_name}
    params.update(additional_params)
    
    # Format the template
    try:
        formatted_prompt = template_data['prompt_template'].format(**params)
        return {
            'prompt': formatted_prompt,
            'hashtags': template_data.get('hashtag_suggestions', []),
            'cta_examples': template_data.get('cta_examples', []),
            'best_practices': template_data.get('best_practices', [])
        }
    except KeyError as e:
        return {
            'prompt': f"Create a social media post for {business_name}. " + template_data['prompt_template'],
            'hashtags': template_data.get('hashtag_suggestions', []),
            'cta_examples': template_data.get('cta_examples', []),
            'best_practices': template_data.get('best_practices', [])
        }

def load_feedback_submissions() -> List[Dict[str, Any]]:
    """Legacy wrapper for loading feedback submissions."""
    return get_feedback_manager().load_submissions()

def save_feedback_submission(feedback_data: Dict[str, Any]) -> bool:
    """Legacy wrapper for saving feedback submissions."""
    return get_feedback_manager().save_submission(feedback_data)

def load_app_statistics() -> Dict[str, Any]:
    """Legacy wrapper for loading app statistics."""
    return get_statistics_manager().load_statistics()

def save_app_statistics(stats: Dict[str, Any]) -> bool:
    """Legacy wrapper for saving app statistics."""
    return get_statistics_manager().save_statistics(stats)

def increment_captions_generated(count: int = 3) -> int:
    """Legacy wrapper for incrementing captions generated."""
    return get_statistics_manager().increment_captions_generated(count)

def get_feedback_summary() -> Dict[str, Any]:
    """Legacy wrapper for getting feedback summary."""
    return get_feedback_manager().get_summary()

def export_feedback_data() -> str:
    """Legacy wrapper for exporting feedback data."""
    return get_feedback_manager().export_data()
