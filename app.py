"""
Hugging Face Spaces Entry Point
This file is required for HuggingFace Spaces deployment
"""

# Re-export the FastAPI app
from app.main import app

# This allows HuggingFace to find the app
__all__ = ["app"]
