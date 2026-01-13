#!/usr/bin/env python3
"""
Run script for AutoSpareHub - PythonAnywhere compatible
"""

import os
import sys
from app import create_app

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )