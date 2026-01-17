# test_bot.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime
# Load environment variables
load_dotenv()

# Get credentials from .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

async def main():
    bot = Bot(token=TOKEN)
    
    try:
        # Lấy thông tin bot
        bot_info = await bot.get_me()
        print(f"Bot info: {bot_info.first_name} (@{bot_info.username})")
        
        # Gửi tin nhắn test
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🚀 TEST THÀNH CÔNG!\nBot của Quân đã hoạt động rồi nè!\nThời gian: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parse_mode="Markdown"
        )
        print("Đã gửi tin nhắn test thành công!")
    except Exception as e:
        print("Lỗi:", e)
        print("Gợi ý: Hãy gửi một tin nhắn bất kỳ cho bot trước khi chạy script này!")

if __name__ == "__main__":
    asyncio.run(main())