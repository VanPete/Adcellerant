#!/usr/bin/env python3
"""
Image processing module for editing, validation, and batch processing of images.
"""

import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import streamlit as st

from config.constants import (
    MAX_FILE_SIZE, MIN_RESOLUTION, MAX_RESOLUTION, ALLOWED_FORMATS
)
from utils.helpers import truncate_text

class ImageProcessor:
    """Handles image editing operations like resize, crop, rotate, and filters."""
    
    def __init__(self):
        self.social_media_presets = {
            "Instagram Square (1080×1080)": (1080, 1080),
            "Instagram Portrait (1080×1350)": (1080, 1350),
            "Instagram Story (1080×1920)": (1080, 1920),
            "Facebook Post (1200×630)": (1200, 630),
            "Facebook Cover (1640×859)": (1640, 859),
            "LinkedIn Post (1200×627)": (1200, 627),
            "Twitter Post (1024×512)": (1024, 512),
            "YouTube Thumbnail (1280×720)": (1280, 720)
        }
    
    def resize_image(self, image: Image.Image, width: int, height: int, 
                    maintain_ratio: bool = False) -> Image.Image:
        """Resize an image to specified dimensions.
        
        Args:
            image: PIL Image object
            width: Target width
            height: Target height
            maintain_ratio: Whether to maintain aspect ratio
            
        Returns:
            Resized PIL Image
        """
        if maintain_ratio:
            # Calculate ratio based on width
            original_width, original_height = image.size
            ratio = width / original_width
            height = int(original_height * ratio)
        
        return image.resize((width, height), Image.Resampling.LANCZOS)
    
    def resize_by_percentage(self, image: Image.Image, percentage: int) -> Image.Image:
        """Resize an image by percentage.
        
        Args:
            image: PIL Image object
            percentage: Percentage to resize (100 = original size)
            
        Returns:
            Resized PIL Image
        """
        original_width, original_height = image.size
        new_width = int(original_width * percentage / 100)
        new_height = int(original_height * percentage / 100)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def resize_to_preset(self, image: Image.Image, preset_name: str) -> Image.Image:
        """Resize image to social media preset dimensions.
        
        Args:
            image: PIL Image object
            preset_name: Name of the preset
            
        Returns:
            Resized PIL Image
        """
        if preset_name not in self.social_media_presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        width, height = self.social_media_presets[preset_name]
        return self.resize_image(image, width, height)
    
    def crop_image(self, image: Image.Image, left: int, top: int, 
                  right: int, bottom: int) -> Image.Image:
        """Crop an image to specified coordinates.
        
        Args:
            image: PIL Image object
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate
            
        Returns:
            Cropped PIL Image
        """
        return image.crop((left, top, right, bottom))
    
    def crop_to_square_center(self, image: Image.Image) -> Image.Image:
        """Crop image to square from center.
        
        Args:
            image: PIL Image object
            
        Returns:
            Square cropped PIL Image
        """
        width, height = image.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        return self.crop_image(image, left, top, right, bottom)
    
    def crop_remove_border(self, image: Image.Image, border_percent: float = 0.1) -> Image.Image:
        """Remove border percentage from all sides.
        
        Args:
            image: PIL Image object
            border_percent: Percentage of border to remove (0.1 = 10%)
            
        Returns:
            Cropped PIL Image
        """
        width, height = image.size
        margin_x = int(width * border_percent)
        margin_y = int(height * border_percent)
        
        return self.crop_image(image, margin_x, margin_y, width - margin_x, height - margin_y)
    
    def rotate_image(self, image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
        """Rotate an image by specified angle.
        
        Args:
            image: PIL Image object
            angle: Rotation angle in degrees (positive = clockwise)
            expand: Whether to expand canvas to fit rotated image
            
        Returns:
            Rotated PIL Image
        """
        # PIL uses negative angles for clockwise rotation
        return image.rotate(-angle, expand=expand, fillcolor='white')
    
    def flip_horizontal(self, image: Image.Image) -> Image.Image:
        """Flip image horizontally.
        
        Args:
            image: PIL Image object
            
        Returns:
            Flipped PIL Image
        """
        return image.transpose(Image.FLIP_LEFT_RIGHT)
    
    def flip_vertical(self, image: Image.Image) -> Image.Image:
        """Flip image vertically.
        
        Args:
            image: PIL Image object
            
        Returns:
            Flipped PIL Image
        """
        return image.transpose(Image.FLIP_TOP_BOTTOM)
    
    def apply_filter(self, image: Image.Image, filter_type: str) -> Image.Image:
        """Apply a filter to the image.
        
        Args:
            image: PIL Image object
            filter_type: Type of filter to apply
            
        Returns:
            Filtered PIL Image
        """
        filtered_image = image.copy()
        
        if filter_type == "Grayscale":
            filtered_image = filtered_image.convert('L').convert('RGB')
        
        elif filter_type == "Sepia":
            # Convert to grayscale first
            grayscale = filtered_image.convert('L')
            # Create sepia effect
            sepia = Image.new('RGB', filtered_image.size, (210, 180, 140))
            filtered_image = Image.blend(Image.new('RGB', filtered_image.size, (255, 255, 255)), sepia, 0.3)
            filtered_image = Image.blend(filtered_image, grayscale.convert('RGB'), 0.7)
        
        elif filter_type == "High Contrast":
            enhancer = ImageEnhance.Contrast(filtered_image)
            filtered_image = enhancer.enhance(1.5)
        
        elif filter_type == "Soft Blur":
            filtered_image = filtered_image.filter(ImageFilter.BLUR)
        
        elif filter_type == "Sharpen":
            filtered_image = filtered_image.filter(ImageFilter.SHARPEN)
        
        elif filter_type == "Edge Enhance":
            filtered_image = filtered_image.filter(ImageFilter.EDGE_ENHANCE)
        
        return filtered_image
    
    def add_watermark(self, image: Image.Image, text: str, position: str = "Bottom Right", 
                     font_size: Optional[int] = None) -> Image.Image:
        """Add text watermark to image.
        
        Args:
            image: PIL Image object
            text: Watermark text
            position: Position of watermark
            font_size: Font size (auto-calculated if None)
            
        Returns:
            Image with watermark
        """
        watermarked_img = image.copy()
        draw = ImageDraw.Draw(watermarked_img)
        
        # Calculate font size based on image dimensions
        img_width, img_height = watermarked_img.size
        if font_size is None:
            font_size = max(12, min(img_width, img_height) // 40)
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        margin = 10
        if position == "Bottom Right":
            pos = (img_width - text_width - margin, img_height - text_height - margin)
        elif position == "Bottom Left":
            pos = (margin, img_height - text_height - margin)
        elif position == "Top Right":
            pos = (img_width - text_width - margin, margin)
        elif position == "Top Left":
            pos = (margin, margin)
        else:  # Center
            pos = ((img_width - text_width) // 2, (img_height - text_height) // 2)
        
        # Add semi-transparent background
        background_margin = 5
        background_bbox = [
            pos[0] - background_margin,
            pos[1] - background_margin,
            pos[0] + text_width + background_margin,
            pos[1] + text_height + background_margin
        ]
        
        # Create overlay for transparency
        overlay = Image.new('RGBA', watermarked_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(background_bbox, fill=(0, 0, 0, 128))
        
        # Composite the overlay
        if watermarked_img.mode != 'RGBA':
            watermarked_img = watermarked_img.convert('RGBA')
        watermarked_img = Image.alpha_composite(watermarked_img, overlay)
        
        # Draw the text
        final_draw = ImageDraw.Draw(watermarked_img)
        final_draw.text(pos, text, font=font, fill=(255, 255, 255, 255))
        
        return watermarked_img
    
    def convert_format(self, image: Image.Image, target_format: str, 
                      quality: int = 90) -> Tuple[io.BytesIO, str]:
        """Convert image to specified format.
        
        Args:
            image: PIL Image object
            target_format: Target format (PNG, JPEG, WebP)
            quality: Quality for lossy formats
            
        Returns:
            Tuple of (BytesIO buffer, file extension)
        """
        img_buffer = io.BytesIO()
        
        format_map = {
            "PNG": ("PNG", "png"),
            "JPEG": ("JPEG", "jpg"),
            "WebP": ("WebP", "webp")
        }
        
        format_key, extension = format_map.get(target_format, ("PNG", "png"))
        
        if format_key == "JPEG":
            # Convert to RGB if necessary for JPEG
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                rgb_image.save(img_buffer, format=format_key, quality=quality)
            else:
                image.save(img_buffer, format=format_key, quality=quality)
        else:
            image.save(img_buffer, format=format_key)
        
        img_buffer.seek(0)
        return img_buffer, extension

class ImageValidator:
    """Validates image files for upload and processing."""
    
    def __init__(self):
        self.max_file_size = MAX_FILE_SIZE
        self.min_resolution = MIN_RESOLUTION
        self.max_resolution = MAX_RESOLUTION
        self.allowed_formats = ALLOWED_FORMATS
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate an uploaded file.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (is_valid, message, file_info)
        """
        try:
            # File size validation
            file_size = uploaded_file.size
            if file_size > self.max_file_size:
                return False, f"File too large ({file_size / 1024 / 1024:.1f}MB > 50MB)", None
            
            if file_size < 1024:  # Less than 1KB
                return False, f"File too small ({file_size} bytes)", None
            
            # Try to open image
            image = Image.open(uploaded_file)
            
            # Format validation
            if image.format not in self.allowed_formats:
                return False, f"Unsupported format ({image.format})", None
            
            # Resolution validation
            width, height = image.size
            if width < self.min_resolution[0] or height < self.min_resolution[1]:
                return False, f"Resolution too low ({width}×{height} < {self.min_resolution[0]}×{self.min_resolution[1]})", None
            
            if width > self.max_resolution[0] or height > self.max_resolution[1]:
                # Warning but still valid
                pass
            
            # File info
            file_info = {
                'image': image,
                'filename': uploaded_file.name,
                'size': image.size,
                'file_size': file_size,
                'format': image.format,
                'mode': image.mode,
                'megapixels': (width * height) / 1000000,
                'aspect_ratio': width / height
            }
            
            return True, "Valid image file", file_info
            
        except Exception as e:
            return False, f"Invalid image file ({str(e)})", None
    
    def validate_batch_files(self, uploaded_files) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """Validate multiple uploaded files for batch processing.
        
        Args:
            uploaded_files: List of Streamlit uploaded file objects
            
        Returns:
            Tuple of (valid_images, validation_errors, processing_warnings)
        """
        valid_images = []
        validation_errors = []
        processing_warnings = []
        
        for uploaded_file in uploaded_files:
            is_valid, message, file_info = self.validate_file(uploaded_file)
            
            if is_valid and file_info:
                # Additional checks for warnings
                width, height = file_info['size']
                
                if width > self.max_resolution[0] or height > self.max_resolution[1]:
                    processing_warnings.append(f"⚠️ {uploaded_file.name}: Very high resolution ({width}×{height}), may slow processing")
                
                # Check for animated images
                if hasattr(file_info['image'], 'is_animated') and file_info['image'].is_animated:
                    processing_warnings.append(f"ℹ️ {uploaded_file.name}: Animated image detected, using first frame")
                    file_info['image'].seek(0)  # Use first frame
                
                # Color mode conversion if needed
                original_mode = file_info['image'].mode
                if file_info['image'].mode not in ['RGB', 'RGBA']:
                    file_info['image'] = file_info['image'].convert('RGB')
                    processing_warnings.append(f"ℹ️ {uploaded_file.name}: Converted from {original_mode} to RGB")
                    file_info['original_mode'] = original_mode
                
                valid_images.append(file_info)
            else:
                validation_errors.append(f"❌ {uploaded_file.name}: {message}")
        
        return valid_images, validation_errors, processing_warnings

class BatchImageProcessor:
    """Handles batch processing operations on multiple images."""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    def process_batch_resize(self, images: List[Dict[str, Any]], target_width: int, 
                           target_height: int) -> List[Dict[str, Any]]:
        """Resize all images in batch to same dimensions.
        
        Args:
            images: List of image dictionaries
            target_width: Target width
            target_height: Target height
            
        Returns:
            List of processed image dictionaries
        """
        processed_images = []
        
        for img_data in images:
            try:
                resized_image = self.image_processor.resize_image(
                    img_data['image'], target_width, target_height
                )
                
                processed_images.append({
                    'image': resized_image,
                    'filename': img_data['filename'],
                    'size': resized_image.size,
                    'processed': True,
                    'operation': f'Resized to {target_width}×{target_height}'
                })
            except Exception as e:
                # Keep original if processing fails
                img_data['processing_error'] = str(e)
                processed_images.append(img_data)
        
        return processed_images
    
    def process_batch_watermark(self, images: List[Dict[str, Any]], watermark_text: str, 
                               position: str = "Bottom Right") -> List[Dict[str, Any]]:
        """Add watermark to all images in batch.
        
        Args:
            images: List of image dictionaries
            watermark_text: Text to add as watermark
            position: Position of watermark
            
        Returns:
            List of processed image dictionaries
        """
        processed_images = []
        
        for img_data in images:
            try:
                watermarked_image = self.image_processor.add_watermark(
                    img_data['image'], watermark_text, position
                )
                
                # Convert back to original mode if needed
                if 'original_mode' in img_data and img_data['original_mode'] != 'RGBA':
                    watermarked_image = watermarked_image.convert(img_data['original_mode'])
                
                processed_images.append({
                    'image': watermarked_image,
                    'filename': img_data['filename'],
                    'size': watermarked_image.size,
                    'processed': True,
                    'operation': f'Added watermark: {watermark_text}'
                })
            except Exception as e:
                # Keep original if processing fails
                img_data['processing_error'] = str(e)
                processed_images.append(img_data)
        
        return processed_images
    
    def get_batch_statistics(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about a batch of images.
        
        Args:
            images: List of image dictionaries
            
        Returns:
            Dictionary containing batch statistics
        """
        if not images:
            return {
                'total_images': 0,
                'total_size_mb': 0,
                'avg_resolution': '0×0',
                'formats': {},
                'color_modes': {}
            }
        
        total_size = sum(img.get('file_size', 0) for img in images) / 1024 / 1024
        avg_megapixels = sum(img.get('megapixels', 0) for img in images) / len(images)
        
        # Count formats and color modes
        formats = {}
        color_modes = {}
        
        for img in images:
            fmt = img.get('format', 'Unknown')
            mode = img.get('mode', 'Unknown')
            
            formats[fmt] = formats.get(fmt, 0) + 1
            color_modes[mode] = color_modes.get(mode, 0) + 1
        
        # Calculate average resolution
        total_pixels = sum(img['size'][0] * img['size'][1] for img in images)
        avg_pixels = total_pixels / len(images)
        
        return {
            'total_images': len(images),
            'total_size_mb': round(total_size, 1),
            'avg_resolution': f"{avg_megapixels:.1f}MP",
            'avg_pixels': int(avg_pixels),
            'formats': formats,
            'color_modes': color_modes,
            'unique_resolutions': len(set(f"{img['size'][0]}×{img['size'][1]}" for img in images))
        }

# Convenience functions for easy access
def get_image_processor() -> ImageProcessor:
    """Get an ImageProcessor instance."""
    return ImageProcessor()

def get_image_validator() -> ImageValidator:
    """Get an ImageValidator instance."""
    return ImageValidator()

def get_batch_processor() -> BatchImageProcessor:
    """Get a BatchImageProcessor instance."""
    return BatchImageProcessor()

# Legacy function wrappers for backward compatibility
def resize_image(image: Image.Image, width: int, height: int, maintain_ratio: bool = False) -> Image.Image:
    """Legacy wrapper for image resizing."""
    return get_image_processor().resize_image(image, width, height, maintain_ratio)

def crop_image(image: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
    """Legacy wrapper for image cropping."""
    return get_image_processor().crop_image(image, left, top, right, bottom)

def rotate_image(image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    """Legacy wrapper for image rotation."""
    return get_image_processor().rotate_image(image, angle, expand)

def apply_filter(image: Image.Image, filter_type: str) -> Image.Image:
    """Legacy wrapper for applying filters."""
    return get_image_processor().apply_filter(image, filter_type)
