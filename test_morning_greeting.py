#!/usr/bin/env python3
# Test morning greeting functionality

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from working_chat_bot import TaskReminder

async def test_morning_greeting():
    """Test the morning greeting functionality"""
    print("Testing morning greeting functionality...")
    
    # Create a mock bot
    class MockBot:
        async def send_message(self, chat_id, text):
            print(f"MOCK: Sending message to {chat_id}: {text}")
            return True
    
    # Initialize reminder
    reminder = TaskReminder()
    reminder.bot = MockBot()
    
    # Test sending morning greeting
    user_id = 123456789  # Test user ID
    success = await reminder.send_morning_greeting(user_id)
    
    if success:
        print("✅ Morning greeting test successful!")
    else:
        print("❌ Morning greeting test failed!")
    
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_morning_greeting())
