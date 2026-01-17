# reminder_bot.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime, timedelta
import re

# Load environment variables
load_dotenv()

# Get credentials from .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

class TaskReminder:
    def __init__(self):
        self.tasks = []
        self.reminded_tasks = set()  # Track tasks that have been reminded
        
    def parse_task_line(self, line):
        """Parse task line format: link  order_id  input_date  deadline"""
        parts = line.split('\t')
        if len(parts) >= 4:
            return {
                'link': parts[0].strip(),
                'order_id': parts[1].strip(),
                'input_date': parts[2].strip(),
                'deadline': parts[3].strip(),
                'raw_line': line.strip()
            }
        return None
    
    def parse_deadline(self, deadline_str):
        """Parse deadline format like '13H 17/1'"""
        try:
            # Extract time and date
            match = re.match(r'(\d+)H\s+(\d+)/(\d+)', deadline_str.strip())
            if match:
                hour = int(match.group(1))
                day = int(match.group(2))
                month = int(match.group(3))
                
                # Get current year and month
                now = datetime.now()
                current_year = now.year
                current_month = now.month
                
                # Create datetime object for current year
                deadline_dt = datetime(current_year, month, day, hour, 0, 0)
                
                # If deadline month is earlier than current month, assume next year
                # If same month but day is earlier, also assume next year
                if month < current_month or (month == current_month and deadline_dt < now):
                    deadline_dt = datetime(current_year + 1, month, day, hour, 0, 0)
                
                return deadline_dt
        except Exception as e:
            print(f"Error parsing deadline '{deadline_str}': {e}")
        return None
    
    def add_tasks_from_text(self, text):
        """Add tasks from multiline text"""
        lines = text.strip().split('\n')
        for line in lines:
            task = self.parse_task_line(line)
            if task:
                deadline_dt = self.parse_deadline(task['deadline'])
                if deadline_dt:
                    task['deadline_dt'] = deadline_dt
                    self.tasks.append(task)
                    print(f"Added task: {task['order_id']} - Deadline: {deadline_dt}")
    
    def check_reminders(self):
        """Check for tasks that need reminder (30 minutes before deadline)"""
        now = datetime.now()
        reminders = []
        
        for task in self.tasks:
            task_key = f"{task['order_id']}_{task['deadline']}"
            
            # Skip if already reminded
            if task_key in self.reminded_tasks:
                continue
            
            deadline_dt = task['deadline_dt']
            reminder_time = deadline_dt - timedelta(minutes=30)
            
            # Check if it's time to remind (within 1 minute window)
            if abs((now - reminder_time).total_seconds()) < 60:
                reminders.append(task)
                self.reminded_tasks.add(task_key)
        
        return reminders
    
    async def send_reminder(self, bot, task):
        """Send reminder message for a task"""
        message = f"⏰ **NHẮC NHỞ ĐƠN HÀNG**\n\n"
        message += f"📋 **Mã đơn:** {task['order_id']}\n"
        message += f"📅 **Deadline:** {task['deadline']}\n"
        message += f"🔗 **Link xử lý:** {task['link']}\n\n"
        message += f"⚠️ Còn 30 phút nữa đến deadline!"
        
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
            print(f"Sent reminder for order: {task['order_id']}")
        except Exception as e:
            print(f"Error sending reminder: {e}")

async def main():
    bot = Bot(token=TOKEN)
    reminder = TaskReminder()
    
    # Read tasks from file
    try:
        with open('tasks.txt', 'r', encoding='utf-8') as f:
            tasks_text = f.read()
        reminder.add_tasks_from_text(tasks_text)
    except FileNotFoundError:
        print("Error: tasks.txt file not found!")
        return
    except Exception as e:
        print(f"Error reading tasks file: {e}")
        return
    
    print(f"Loaded {len(reminder.tasks)} tasks")
    print("Bot is running... Checking for reminders every 30 seconds")
    
    try:
        while True:
            # Check for reminders
            reminders = reminder.check_reminders()
            
            # Send reminders
            for task in reminders:
                await reminder.send_reminder(bot, task)
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
