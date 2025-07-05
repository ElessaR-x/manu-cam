#!/usr/bin/env python3
"""
📹 Kamera API - Koyeb Deployment
"""

import sys
import os

# API dizinini Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

# FastAPI uygulamasını import et
from main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 