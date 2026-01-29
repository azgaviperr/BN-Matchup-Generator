# coding: utf-8
"""
Utility functions for file operations and text processing.
"""

import os
import re
import unicodedata
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def remove_accents(text: str) -> str:
    """
    Remove accents from a string.
    
    Args:
        text: Input string with accents
        
    Returns:
        String without accents
    """
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing accents and invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystems
    """
    # Remove accents
    filename = remove_accents(filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    return filename


def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        The path that was created/verified
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")
    return path


def get_unique_filename(base_path: str, extension: str = "", max_tries: int = 9999) -> str:
    """
    Get a unique filename by appending a number if file exists.
    
    Args:
        base_path: Base file path without extension
        extension: File extension (with or without dot)
        max_tries: Maximum number of attempts before raising an error
        
    Returns:
        Unique filename
        
    Raises:
        RuntimeError: If max_tries is exceeded
    """
    if not extension.startswith('.') and extension:
        extension = f'.{extension}'
    
    path = f"{base_path}{extension}"
    
    if not os.path.exists(path):
        return path
    
    for counter in range(1, max_tries + 1):
        path = f"{base_path}_{counter}{extension}"
        if not os.path.exists(path):
            return path
    
    raise RuntimeError(f"Could not find unique filename after {max_tries} attempts")


def format_match_string(team1: str, team2: str, separator: str = "vs") -> str:
    """
    Format a match string consistently.
    
    Args:
        team1: First team name
        team2: Second team name
        separator: Separator string (default: "vs")
        
    Returns:
        Formatted match string
    """
    return f"{team1} {separator} {team2}"


def parse_day_number(day_string: str) -> Optional[int]:
    """
    Extract the day number from a day string like "Journée 1".
    
    Args:
        day_string: String containing day information
        
    Returns:
        Day number or None if not found
    """
    match = re.search(r'\d+', day_string)
    return int(match.group()) if match else None
