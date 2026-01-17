# Deploy Bot Telegram lên Server

## Cách deploy bot chạy 24/7

### 1. Chuẩn bị Server
- **VPS/Cloud Server:** Ubuntu 20.04+, CentOS 7+
- **Python 3.8+**
- **Internet ổn định**
- **Port 443 (HTTPS) hoặc 80 (HTTP)**

### 2. Upload code
```bash
# scp toàn bộ thư mục
scp -r telegram_bot/ user@server:/home/user/

# Hoặc dùng git
git clone <repo> telegram_bot
cd telegram_bot
```

### 3. Cài đặt dependencies
```bash
# Cài Python và pip
sudo apt update
sudo apt install python3 python3-pip

# Cài virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài packages
pip install python-telegram-bot python-dotenv
```

### 4. Cấu hình
```bash
# Tạo file .env
nano .env

# Nội dung:
TELEGRAM_BOT_TOKEN=8545812265:AAF3-UTEvg5GDos02ebTFwQgjfdv5UBlg2U
TELEGRAM_CHAT_ID=2035484726
```

### 5. Chạy bot với PM2
```bash
# Cài PM2 (process manager)
npm install -g pm2

# Chạy bot với PM2
pm2 start working_chat_bot.py --name "telegram-bot"

# Kiểm tra status
pm2 status

# Xem log
pm2 logs telegram-bot

# Restart bot
pm2 restart telegram-bot
```

### 6. Cấu hình tự động start
```bash
# Tạo file ecosystem.config.js cho PM2
pm2 ecosystem start ecosystem.config.js

# Nội dung ecosystem.config.js:
module.exports = {
  apps: [{
    name: "telegram-bot",
    script: "working_chat_bot.py",
    interpreter: "python3",
    cwd: "/home/user/telegram_bot",
    autorestart: true,
    watch: false,
    max_memory_restart: "1G",
    env: {
      NODE_ENV: "production"
    }
  }]
}
```

### 7. Test deploy
```bash
# Test bot hoạt động
pm2 logs telegram-bot --lines 50

# Kiểm tra process
ps aux | grep working_chat_bot
```

### 8. Domain (tùy chọn)
```bash
# Cấu hình Nginx nếu cần domain
sudo nano /etc/nginx/sites-available/telegram-bot

# Restart Nginx
sudo systemctl restart nginx
```

## Lợi ích deploy server
- ✅ **24/7 hoạt động:** Không phụ thuộc laptop
- 🔄 **Tự động restart:** Khi crash tự start lại
- 📊 **Monitoring:** Theo dõi log dễ dàng
- ⚡ **Stable:** Internet server ổn định hơn

## Các lựa chọn server
1. **DigitalOcean** - $5/tháng
2. **Vultr** - $3.5/tháng  
3. **Linode** - $5/tháng
4. **AWS EC2** - Free tier 1 năm
5. **Google Cloud** - Free tier $300 credit

## Script deploy nhanh
```bash
#!/bin/bash
# deploy.sh
cd /home/user/telegram_bot
source venv/bin/activate
pm2 stop telegram-bot
pm2 start working_chat_bot.py --name "telegram-bot"
echo "Bot deployed successfully!"
```
