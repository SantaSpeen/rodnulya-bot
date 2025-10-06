#!/usr/bin/env python
"""Simple test script to verify the bot modules can be imported."""
import sys

print("Testing module imports...")

try:
    from src.config import settings
    print("✓ Config module imported successfully")
    
    from src.database import Base, DatabaseManager, User, Subscription, Payment
    print("✓ Database models imported successfully")
    
    from src.http_server import HTTPServer
    print("✓ HTTP server imported successfully")
    
    from src.bot import router
    print("✓ Bot handlers imported successfully")
    
    print("\n✅ All modules imported successfully!")
    print("\nNote: To run the bot, you need to:")
    print("1. Create a .env file with your BOT_TOKEN")
    print("2. Run: python -m src.main")
    
except Exception as e:
    print(f"\n❌ Error during import: {e}")
    sys.exit(1)
