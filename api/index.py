"""
Vercel Serverless Entry Point for agentic-ai FastAPI Backend
============================================================
This file exposes the FastAPI app as a Vercel Python serverless function.
Vercel routes /api/* requests here via vercel.json rewrites.
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import the FastAPI app from main.py
from main import app
