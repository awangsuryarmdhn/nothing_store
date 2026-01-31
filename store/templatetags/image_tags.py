"""
Custom template tags for image optimization.
Usage: {% load image_tags %}
       {{ image.url|webp }}
       {{ image.url|webp:800 }}
"""
from django import template
from django.conf import settings
import re

register = template.Library()


@register.filter
def webp(url, width=None):
    """
    Convert Supabase image URL to WebP format with optional resize.
    Supabase Transform API: /render/image/sign/{path}?format=webp&width=xxx
    
    For S3-direct URLs, we can't transform, so return original.
    """
    if not url:
        return url
    
    # Check if it's a Supabase storage URL
    supabase_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', '')
    
    if supabase_endpoint and supabase_endpoint in str(url):
        # Supabase doesn't have built-in transforms like Cloudinary
        # But we can use their Image Transformation API if enabled
        # For now, just return original URL
        # TODO: Implement Supabase image transforms when available
        return url
    
    return url


@register.filter  
def image_srcset(url, sizes='400,800,1200'):
    """
    Generate srcset for responsive images.
    Usage: {{ image.url|image_srcset:"400,800,1200" }}
    Returns: url?w=400 400w, url?w=800 800w, url?w=1200 1200w
    """
    if not url:
        return ''
    
    size_list = [int(s.strip()) for s in sizes.split(',')]
    srcset_parts = []
    
    for size in size_list:
        # For Supabase, we'd need their transform API
        # For now, just return the original URL with width hint
        srcset_parts.append(f"{url} {size}w")
    
    return ', '.join(srcset_parts)


@register.simple_tag
def optimized_image(url, width=800, height=None, format='webp'):
    """
    Generate optimized image URL.
    Usage: {% optimized_image image.url 800 %}
    """
    if not url:
        return ''
    
    # Return original for now - Supabase transform requires Pro plan
    return url
