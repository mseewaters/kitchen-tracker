"""
Import helper for Lambda environment
Place this file in backend/src/kitchen_tracker/
"""

import os
import sys

def setup_imports():
    """Setup imports to work in both Lambda and local environments"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

# Call this immediately when imported
setup_imports()