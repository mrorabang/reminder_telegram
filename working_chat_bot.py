# working_chat_bot.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import re
import threading
import time

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
        self.bot = None
        
    def set_bot(self, bot):
        """Set bot instance for sending messages"""
        self.bot = bot
        
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
        """Parse task line format: link  order_id  ngay_tao  gio_deadline  ngay_deadline"""
        # Try different separators
        separators = ['|', ',', ';', '  ']  # pipe, comma, semicolon, double space
        
        for sep in separators:
            parts = line.split(sep)
            if len(parts) >= 5:
                # New format: link | order_id | ngay_tao | gio_deadline | ngay_deadline
                gio_deadline = parts[3].strip()
                ngay_deadline = parts[4].strip()
                deadline_full = f"{gio_deadline} {ngay_deadline}"
                
                return {
                    'link': parts[0].strip(),
                    'order_id': parts[1].strip(),
                    'input_date': parts[2].strip(),
                    'gio_deadline': gio_deadline,
                    'ngay_deadline': ngay_deadline,
                    'deadline': deadline_full,
                    'raw_line': line.strip()
                }
            elif len(parts) >= 4:
                # Old format: link | order_id | input_date | deadline
                return {
                    'link': parts[0].strip(),
                    'order_id': parts[1].strip(),
                    'input_date': parts[2].strip(),
                    'deadline': parts[3].strip(),
                    'raw_line': line.strip()
                }
        
        # If no separator found, try to parse by counting parts
        parts = line.split()
        if len(parts) >= 5:
            # New format: link order_id ngay_tao gio_deadline ngay_deadline
            ngay_deadline = parts[-1]
            gio_deadline = parts[-2]
            input_date = parts[-3]
            order_id = parts[-4]
            link = ' '.join(parts[:-4])
            
            deadline_full = f"{gio_deadline} {ngay_deadline}"
            
            return {
                'link': link,
                'order_id': order_id,
                'input_date': input_date,
                'gio_deadline': gio_deadline,
                'ngay_deadline': ngay_deadline,
                'deadline': deadline_full,
                'raw_line': line.strip()
            }
        elif len(parts) >= 4:
            # Old format: link order_id input_date deadline
            deadline = parts[-1]
            input_date = parts[-2]
            order_id = parts[-3]
            link = ' '.join(parts[:-3])
            
            return {
                'link': link,
                'order_id': order_id,
                'input_date': input_date,
                'deadline': deadline,
                'raw_line': line.strip()
            }
        
        return None
    
    def parse_deadline(self, deadline_str):
        """Parse deadline format like '13H 17/1' or '13h30 17/1' or '20h59 17/1/2026'"""
        try:
            # Try format with minutes and full year: 20h59 17/1/2026
            match = re.match(r'(\d+)[hH](\d+)\s+(\d+)/(\d+)/(\d+)', deadline_str.strip())
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                day = int(match.group(3))
                month = int(match.group(4))
                year = int(match.group(5))
            else:
                # Try format with minutes: 13h30 17/1
                match = re.match(r'(\d+)[hH](\d+)\s+(\d+)/(\d+)', deadline_str.strip())
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    day = int(match.group(3))
                    month = int(match.group(4))
                    year = datetime.now().year
                else:
                    # Try format without minutes: 13H 17/1
                    match = re.match(r'(\d+)[hH]\s+(\d+)/(\d+)', deadline_str.strip())
                    if match:
                        hour = int(match.group(1))
                        minute = 0
                        day = int(match.group(2))
                        month = int(match.group(3))
                        year = datetime.now().year
                    else:
                        return None
            
            deadline_dt = datetime(year, month, day, hour, minute, 0)
            
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
                    
                    # Check for EXACT duplicate (all fields) in current tasks
                    if self.is_exact_duplicate(task):
                        return False, f"🚫 REJECT: Ticket này đã tồn tại trong danh sách!"
                    
                    self.tasks.append(task)
                    self.save_tasks()
                    return True, f"✅ Đã thêm công việc: {task['order_id']} - Deadline: {task['deadline']}"
                else:
                    return False, "❌ Không thể đọc deadline. Format: 20h59 17/1/2026 hoặc 13H 17/1"
            else:
                return False, "Format sai: link order_id input_date time_deadline date_deadline"
        except Exception as e:
            return False, f"❌ Lỗi: {e}"
    
    def find_task_by_order_id(self, order_id):
        """Find task by order_id"""
        for task in self.tasks:
            if task['order_id'] == order_id:
                return task
        return None
    
    def is_exact_duplicate(self, new_task):
        """Check if task is exact duplicate of existing task"""
        for existing_task in self.tasks:
            if (existing_task['link'] == new_task['link'] and
                existing_task['order_id'] == new_task['order_id'] and
                existing_task['input_date'] == new_task['input_date'] and
                existing_task['deadline'] == new_task['deadline']):
                return True
        return False
    
    def add_tasks_from_text(self, text):
        """Add tasks from multiline text"""
        lines = text.strip().split('\n')
        for line in lines:
            task = self.parse_task_line(line)
            if task:
                deadline_dt = self.parse_deadline(task['deadline'])
                if deadline_dt:
                    task['deadline_dt'] = deadline_dt
                    # Check for duplicates when loading from file
                    existing_task = self.find_task_by_order_id(task['order_id'])
                    if not existing_task:
                        self.tasks.append(task)
    
    def check_reminders(self):
        """Check for tasks that need reminder (30 minutes before deadline)"""
        now = datetime.now()
        reminders = []
        tasks_to_remove = []
        
        # Group tasks by order_id to avoid duplicate reminders
        processed_order_ids = set()
        
        for task in self.tasks:
            order_id = task['order_id']
            
            # Skip if we already processed this order_id
            if order_id in processed_order_ids:
                continue
            
            task_key = f"{task['order_id']}_{task['deadline']}"
            
            if task_key in self.reminded_tasks:
                processed_order_ids.add(order_id)
                continue
            
            deadline_dt = task['deadline_dt']
            reminder_time = deadline_dt - timedelta(minutes=30)
            
            if abs((now - reminder_time).total_seconds()) < 60:
                reminders.append(task)
                self.reminded_tasks.add(task_key)
                processed_order_ids.add(order_id)
                tasks_to_remove.append(task)
        
        # Remove tasks that were reminded
        for task in tasks_to_remove:
            self.tasks.remove(task)
            print(f"🗑️ Đã xóa ticket {task['order_id']} khỏi danh sách sau khi nhắc hẹn")
        
        if tasks_to_remove:
            self.save_tasks()
        
        return reminders
    
    async def send_reminder(self, task):
        """Send reminder message for a task"""
        if not self.bot:
            return
            
        message = f"⏰ NHẮC NHỞ ĐƠN HÀNG\n\n"
        message += f"📋 Mã đơn: {task['order_id']}\n"
        message += f"📅 Deadline: {task['deadline']}\n"
        message += f"🔗 Link xử lý: {task['link']}\n\n"
        message += f"⚠️ Còn 30 phút nữa đến deadline!"
        
        try:
            await self.bot.send_message(
                chat_id=CHAT_ID,
                text=message
            )
            print(f"Sent reminder for order: {task['order_id']}")
        except Exception as e:
            print(f"Error sending reminder: {e}")

# Global reminder instance
reminder = TaskReminder()

def reminder_checker_thread():
    """Background thread to check reminders"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            reminders = reminder.check_reminders()
            
            if reminders and reminder.bot:
                for task in reminders:
                    loop.run_until_complete(reminder.send_reminder(task))
            
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in reminder checker: {e}")
            time.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 Bot Nhắc Hẹn Công Việc\n\n"
        "📝 Cách thêm công việc:\n"
        "Gửi tin nhắn với format:\n"
        "link | mã đơn | ngày_tạo | giờ_deadline | ngày_deadline\n"
        "link , mã đơn , ngày_tạo , giờ_deadline , ngày_deadline\n"
        "link ; mã đơn ; ngày_tạo ; giờ_deadline ; ngày_deadline\n"
        "Hoặc: link mã đơn ngày_tạo giờ_deadline ngày_deadline\n\n"
        "📅 Format deadline: 20h59 17/1/2026 (20 giờ 59 phút ngày 17/1/2026)\n"
        "📅 Format cũ: 13H 17/1 hoặc 13h30 17/1 (vẫn hỗ trợ)\n\n"
        "📋 Các lệnh:\n"
        "/start - Hiển thị hướng dẫn\n"
        "/list - Xem danh sách công việc\n"
        "/help - Trợ giúp\n\n"
        "Bot sẽ tự động nhắc hẹn 30 phút trước deadline!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        "📖 Trợ giúp Bot Nhắc Hẹn\n\n"
        "🔹 Thêm công việc:\n"
        "https://link.com | VNGH123 | 16/1/2026 | 20h59 | 17/1/2026\n"
        "https://link.com , VNGH123 , 16/1/2026 , 20h59 , 17/1/2026\n"
        "https://link.com ; VNGH123 ; 16/1/2026 ; 20h59 ; 17/1/2026\n"
        "https://link.com VNGH123 16/1/2026 20h59 17/1/2026\n\n"
        "🔹 Format cũ (vẫn hỗ trợ):\n"
        "https://link.com | VNGH123 | 16-thg 1 | 13H 17/1\n\n"
        "🔹 Xem danh sách: /list\n"
        "🔹 Nhắc hẹn: Tự động 30 phút trước deadline\n\n"
        "⚠️ Lưu ý: Dùng | , ; hoặc space để phân cách các cột"
    )

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command"""
    if not reminder.tasks:
        await update.message.reply_text("📭 Không có công việc nào trong danh sách")
        return
    
    message = "📋 Danh sách công việc:\n\n"
    for i, task in enumerate(reminder.tasks, 1):
        message += f"{i}. {task['order_id']} - {task['deadline']}\n"
        message += f"   🔗 {task['link']}\n\n"
    
    await update.message.reply_text(message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    message_text = update.message.text
    
    # Debug: print actual message received
    print(f"Received message: '{message_text}'")
    print(f"Message length: {len(message_text)}")
    print(f"Message bytes: {message_text.encode('utf-8')}")
    
    # Check if message contains multiple lines
    if '\n' in message_text:
        # Handle multiline message
        added_count = 0
        duplicate_count = 0
        error_count = 0
        
        lines = message_text.strip().split('\n')
        for line in lines:
            if line.strip():  # Skip empty lines
                success, response = reminder.add_task_from_message(line.strip())
                if success:
                    added_count += 1
                elif "REJECT" in response:
                    duplicate_count += 1
                else:
                    error_count += 1
        
        # response_msg = f"📊 Kết quả:\n"
        response_msg += f"✅ Thêm thành công: {added_count} tickets\n"
        if duplicate_count > 0:
            response_msg += f"🔄 Trùng lặp: {duplicate_count} tickets\n"
        if error_count > 0:
            response_msg += f"❌ Lỗi: {error_count} tickets"
        
        await update.message.reply_text(response_msg)
    else:
        # Handle single line message
        success, response = reminder.add_task_from_message(message_text)
        await update.message.reply_text(response)

async def post_init(application: Application) -> None:
    """Initialize after bot starts"""
    # Set bot instance for reminder
    reminder.set_bot(application.bot)
    
    # Start reminder checker thread
    reminder_thread = threading.Thread(target=reminder_checker_thread, daemon=True)
    reminder_thread.start()
    print("Reminder checker thread started")

def main():
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
    print("Reminder checker running in background thread...")
    
    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
