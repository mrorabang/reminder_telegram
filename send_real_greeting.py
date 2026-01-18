#!/usr/bin/env python3
# Send test morning greeting immediately

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from working_chat_bot import TaskReminder
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

# Get credentials from .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

async def send_real_greeting():
    """Send real morning greeting to Telegram"""
    print("Sending real morning greeting to Telegram...")
    
    try:
        # Create real bot
        bot = Bot(token=TOKEN)
        
        # Initialize reminder
        reminder = TaskReminder()
        reminder.bot = bot
        
        # Send greeting
        message = "Chào người đẹp của anh , chúc người đẹp ngày mới nhiều năng lượng và vui vẻ , nhớ nhắn cho anh nhé. Yêu người đẹp nhiều  ❤️"
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        
        print("✅ Greeting sent successfully to Telegram!")
        print(f"Message: {message}")
        
    except Exception as e:
        print(f"❌ Error sending greeting: {e}")
        print("Make sure:")
        print("1. TELEGRAM_BOT_TOKEN is correct in .env file")
        print("2. TELEGRAM_CHAT_ID is correct in .env file")
        print("3. Bot has permission to send messages to the chat")

if __name__ == "__main__":
    asyncio.run(send_real_greeting())
