"""
pyJianYingDraft - A Python library for creating and editing JianYing/CapCut drafts.

This library provides a comprehensive interface for programmatically creating and modifying
CapCut (JianYing) video editing drafts. It supports various media types, effects, transitions,
and advanced editing features.

Key Features:
- Create new drafts with custom resolutions
- Add and manipulate video, audio, image, and text tracks
- Apply various effects, transitions, and animations
- Support for stickers, subtitles, and advanced text formatting
- Export drafts for use in CapCut desktop application
- Comprehensive API for all editing operations

Basic Usage:
    from pyJianYingDraft import Draft, Track, VideoSegment, AudioSegment
    
    # Create a new draft
    draft = Draft.create(width=1080, height=1920)
    
    # Add a video track
    video_track = draft.add_track(type='video')
    
    # Add a video segment
    video_segment = VideoSegment('path/to/video.mp4', start=0, duration=10)
    video_track.add_segment(video_segment)
    
    # Save the draft
    draft.save('my_draft.json')

Advanced Features:
- Support for multiple video/audio tracks
- Complex transitions and effects
- Text animations and styling
- Image overlays and animations
- Audio mixing and effects
- Batch operations for efficiency

Dependencies:
- Python 3.7+
- json5 (for enhanced JSON handling)
- Pillow (for image processing)
- numpy (for numerical operations)

Installation:
    pip install pyJianYingDraft

License: MIT
Author: CapCutAPI Contributors
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "CapCutAPI Contributors"
__license__ = "MIT"

# Core classes
from .draft import Draft
from .track import Track
from .segment import (
    Segment, VideoSegment, AudioSegment, ImageSegment, TextSegment
)
from .effect import Effect, TransitionEffect, FilterEffect
from .text import TextStyle, TextAnimation
from .utils import (
    generate_uuid, validate_color, format_duration, 
    parse_duration, convert_to_capcut_format
)

# Convenience functions
from .draft import create_draft, load_draft, save_draft
from .templates import get_template, list_templates

# Constants
from .constants import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_FPS,
    VIDEO_CODECS, AUDIO_CODECS, SUPPORTED_FORMATS,
    EFFECT_TYPES, TRANSITION_TYPES, ANIMATION_TYPES
)

# Version info
__all__ = [
    # Core classes
    'Draft', 'Track', 'Segment', 'VideoSegment', 'AudioSegment',
    'ImageSegment', 'TextSegment', 'Effect', 'TransitionEffect',
    'FilterEffect', 'TextStyle', 'TextAnimation',
    
    # Functions
    'create_draft', 'load_draft', 'save_draft',
    'get_template', 'list_templates',
    
    # Utilities
    'generate_uuid', 'validate_color', 'format_duration',
    'parse_duration', 'convert_to_capcut_format',
    
    # Constants
    'DEFAULT_WIDTH', 'DEFAULT_HEIGHT', 'DEFAULT_FPS',
    'VIDEO_CODECS', 'AUDIO_CODECS', 'SUPPORTED_FORMATS',
    'EFFECT_TYPES', 'TRANSITION_TYPES', 'ANIMATION_TYPES',
]

# Initialize logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Check for optional dependencies
try:
    import PIL
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("Pillow not found. Image processing features will be limited.")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("NumPy not found. Some numerical operations may be slower.")

# Initialize default settings
default_settings = {
    'width': DEFAULT_WIDTH,
    'height': DEFAULT_HEIGHT,
    'fps': DEFAULT_FPS,
    'video_codec': VIDEO_CODECS[0],
    'audio_codec': AUDIO_CODECS[0],
    'quality': 'high',
    'enable_hardware_acceleration': True,
    'enable_multithreading': True,
}

# Create default directories
def _setup_directories():
    """Setup necessary directories for the library."""
    import os
    from pathlib import Path
    
    # Create user directories
    home_dir = Path.home()
    
    # Draft storage directory
    drafts_dir = home_dir / '.capcut_drafts'
    drafts_dir.mkdir(exist_ok=True)
    
    # Temporary directory
    temp_dir = home_dir / '.capcut_temp'
    temp_dir.mkdir(exist_ok=True)
    
    # Cache directory
    cache_dir = home_dir / '.capcut_cache'
    cache_dir.mkdir(exist_ok=True)
    
    return {
        'drafts': str(drafts_dir),
        'temp': str(temp_dir),
        'cache': str(cache_dir)
    }

# Initialize directories on import
_directories = _setup_directories()

# Utility function to get directory paths
def get_drafts_directory():
    """Get the path to the drafts directory."""
    return _directories['drafts']

def get_temp_directory():
    """Get the path to the temporary directory."""
    return _directories['temp']

def get_cache_directory():
    """Get the path to the cache directory."""
    return _directories['cache']

# Initialize the library
print(f"pyJianYingDraft v{__version__} initialized")
print(f"Drafts directory: {get_drafts_directory()}")
print(f"Temp directory: {get_temp_directory()}")
print(f"Cache directory: {get_cache_directory()}")

# Check for updates (optional)
def check_updates():
    """Check for library updates (requires internet)."""
    try:
        import requests
        response = requests.get('https://pypi.org/pypi/pyJianYingDraft/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data['info']['version']
            if latest_version != __version__:
                print(f"Update available: v{latest_version} (current: v{__version__})")
    except Exception:
        pass  # Silently fail if no internet

# Uncomment to enable update checking on import
# check_updates()