# chat_reminder_bot.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
        self.reminded_tasks = set()
        self.tasks_file = 'tasks.txt'
        
    def load_tasks(self):
        """Load tasks from file"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_text = f.read()
            self.add_tasks_from_text(tasks_text)
            print(f"Loaded {len(self.tasks)} tasks from file")
        except FileNotFoundError:
            print("No tasks file found, starting fresh")
        except Exception as e:
            print(f"Error loading tasks: {e}")
    
    def save_tasks(self):
        """Save tasks to file"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                for task in self.tasks:
                    f.write(task['raw_line'] + '\n')
            print(f"Saved {len(self.tasks)} tasks to file")
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
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
            match = re.match(r'(\d+)H\s+(\d+)/(\d+)', deadline_str.strip())
            if match:
                hour = int(match.group(1))
                day = int(match.group(2))
                month = int(match.group(3))
                
                now = datetime.now()
                current_year = now.year
                current_month = now.month
                
                deadline_dt = datetime(current_year, month, day, hour, 0, 0)
                
                if month < current_month or (month == current_month and deadline_dt < now):
                    deadline_dt = datetime(current_year + 1, month, day, hour, 0, 0)
                
                return deadline_dt
        except Exception as e:
            print(f"Error parsing deadline '{deadline_str}': {e}")
        return None
    
    def add_task_from_message(self, message_text):
        """Add task from chat message"""
        try:
            task = self.parse_task_line(message_text)
            if task:
                deadline_dt = self.parse_deadline(task['deadline'])
                if deadline_dt:
                    task['deadline_dt'] = deadline_dt
                    self.tasks.append(task)
                    self.save_tasks()
                    return True, f"✅ Đã thêm công việc: {task['order_id']} - Deadline: {task['deadline']}"
                else:
                    return False, "❌ Không thể đọc deadline. Format: 13H 17/1"
            else:
                return False, "❌ Format sai. Cần: link<TAB>mã đơn<TAB>ngày<TAB>deadline"
        except Exception as e:
            return False, f"❌ Lỗi: {e}"
    
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
    
    def check_reminders(self):
        """Check for tasks that need reminder (30 minutes before deadline)"""
        now = datetime.now()
        reminders = []
        
        for task in self.tasks:
            task_key = f"{task['order_id']}_{task['deadline']}"
            
            if task_key in self.reminded_tasks:
                continue
            
            deadline_dt = task['deadline_dt']
            reminder_time = deadline_dt - timedelta(minutes=30)
            
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

# Global reminder instance
reminder = TaskReminder()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **Bot Nhắc Hẹn Công Việc**\n\n"
        "📝 **Cách thêm công việc:**\n"
        "Gửi tin nhắn với format:\n"
        "`link<TAB>mã đơn<TAB>ngày<TAB>deadline`\n\n"
        "📅 **Format deadline:** `13H 17/1` (13 giờ ngày 17/1)\n\n"
        "📋 **Các lệnh:**\n"
        "/start - Hiển thị hướng dẫn\n"
        "/list - Xem danh sách công việc\n"
        "/help - Trợ giúp\n\n"
        "Bot sẽ tự động nhắc hẹn 30 phút trước deadline!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        "📖 **Trợ giúp Bot Nhắc Hẹn**\n\n"
        "🔹 **Thêm công việc:**\n"
        "`https://link.com<TAB>VNGH123<TAB>16-thg 1<TAB>13H 17/1`\n\n"
        "🔹 **Xem danh sách:** /list\n"
        "🔹 **Nhắc hẹn:** Tự động 30 phút trước deadline\n\n"
        "⚠️ **Lưu ý:** Dùng TAB (không phải space) để phân cách các cột",
        parse_mode="Markdown"
    )

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command"""
    if not reminder.tasks:
        await update.message.reply_text("📭 Không có công việc nào trong danh sách")
        return
    
    message = "📋 **Danh sách công việc:**\n\n"
    for i, task in enumerate(reminder.tasks, 1):
        message += f"{i}. **{task['order_id']}** - {task['deadline']}\n"
        message += f"   🔗 {task['link']}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    message_text = update.message.text
    
    # Try to add task from message
    success, response = reminder.add_task_from_message(message_text)
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def reminder_checker(app: Application):
    """Background task to check reminders"""
    while True:
        try:
            reminders = reminder.check_reminders()
            
            for task in reminders:
                await reminder.send_reminder(app.bot, task)
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in reminder checker: {e}")
            await asyncio.sleep(30)

async def post_init(application: Application) -> None:
    """Initialize after bot starts"""
    # Start reminder checker in background
    asyncio.create_task(reminder_checker(application))

async def main():
    """Start the bot"""
    # Load existing tasks
    reminder.load_tasks()
    
    # Create application
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot started successfully!")
    print("Commands: /start, /help, /list")
    print("Reminder checker will start after bot initialization...")
    
    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
