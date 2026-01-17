# test_reminder.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime, timedelta
from working_chat_bot import TaskReminder

# Load environment variables
load_dotenv()

# Get credentials from .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

async def test_reminder():
    bot = Bot(token=TOKEN)
    reminder = TaskReminder()
    
    # Read tasks from file
    try:
        with open('tasks.txt', 'r', encoding='utf-8') as f:
            tasks_text = f.read()
        reminder.add_tasks_from_text(tasks_text)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    print(f"Loaded {len(reminder.tasks)} tasks")
    
    # Show all tasks with deadlines
    print("\n=== TASKS ===")
    for task in reminder.tasks:
        print(f"Order: {task['order_id']} | Deadline: {task['deadline']} | DateTime: {task['deadline_dt']}")
    
    # Send test reminder for first task
    if reminder.tasks:
        print(f"\nSending test reminder for: {reminder.tasks[0]['order_id']}")
        reminder.set_bot(bot)
        await reminder.send_reminder(reminder.tasks[0])
    else:
        print("No tasks found")

if __name__ == "__main__":
    asyncio.run(test_reminder())
