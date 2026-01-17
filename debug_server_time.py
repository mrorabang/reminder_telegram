#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def debug_server_time():
    print("🔍 DEBUG SERVER TIME ISSUES")
    print("=" * 50)
    
    # 1. Check current server time
    now = datetime.now()
    print(f"🕐 Server time: {now}")
    print(f"📅 Date: {now.strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {now.strftime('%H:%M:%S')}")
    print(f"🌍 Timezone: {now.tzinfo}")
    
    # 2. Check system timezone
    try:
        import time
        tz = time.tzname
        print(f"🌐 System timezone: {tz}")
    except:
        print("❌ Cannot get system timezone")
    
    # 3. Test deadline parsing
    print("\n📋 TEST DEADLINE PARSING:")
    test_deadlines = [
        "20h59 17/1/2026",
        "23h30 18/1/2026", 
        "00h30 19/1/2026"
    ]
    
    for deadline_str in test_deadlines:
        try:
            # Simulate parsing logic
            import re
            match = re.match(r'(\d+)[hH](\d+)\s+(\d+)/(\d+)/(\d+)', deadline_str)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                day = int(match.group(3))
                month = int(match.group(4))
                year = int(match.group(5))
                
                deadline_dt = datetime(year, month, day, hour, minute, 0)
                reminder_time = deadline_dt - timedelta(minutes=30)
                
                print(f"📅 {deadline_str}")
                print(f"   Deadline: {deadline_dt}")
                print(f"   Reminder: {reminder_time}")
                print(f"   Time diff: {(now - reminder_time).total_seconds() / 60:.1f} minutes")
                print(f"   Should remind: {abs((now - reminder_time).total_seconds()) < 60}")
                print()
        except Exception as e:
            print(f"❌ Error parsing {deadline_str}: {e}")
    
    # 4. Check environment
    print("🔧 ENVIRONMENT CHECK:")
    print(f"🐍 Python version: {os.sys.version}")
    print(f"📁 Working dir: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")
    
    # 5. Check files
    print("\n📁 FILES CHECK:")
    if os.path.exists('.env'):
        print("✅ .env file exists")
        with open('.env', 'r') as f:
            print(f"   Token: {f.readline().strip()[:20]}...")
            print(f"   Chat ID: {f.readline().strip()}")
    else:
        print("❌ .env file missing")
    
    if os.path.exists('tasks.txt'):
        with open('tasks.txt', 'r') as f:
            tasks = f.readlines()
            print(f"✅ tasks.txt exists ({len(tasks)} lines)")
            if tasks:
                print(f"   First task: {tasks[0].strip()}")
    else:
        print("❌ tasks.txt missing")
    
    # 6. Network test
    print("\n🌐 NETWORK TEST:")
    try:
        import requests
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            print(f"✅ Telegram API: {response.status_code}")
            if response.status_code == 200:
                bot_info = response.json()
                print(f"   Bot: @{bot_info['result']['username']}")
            else:
                print(f"❌ API Error: {response.text}")
        else:
            print("❌ No token found")
    except Exception as e:
        print(f"❌ Network error: {e}")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. Set timezone: sudo timedatectl set-timezone Asia/Ho_Chi_Minh")
    print("2. Check server time vs local time")
    print("3. Test with deadline within 1 hour")
    print("4. Monitor logs: tail -f bot.log")

if __name__ == "__main__":
    debug_server_time()
