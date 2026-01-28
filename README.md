# 🚀 Telegram Job Alert Bot

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Web%20Framework-blueviolet)
![Render](https://img.shields.io/badge/Deploy-Render-purple)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-Production-brightgreen)

A **production-ready Telegram bot** that automatically sends:

✅ Jobs  
✅ Internships  
✅ Remote work  
✅ Scholarships  

directly to students every day.

---

## ✨ Features

### 🎯 For Users
- **/start** registration with user-friendly onboarding
- **Category selection** (Jobs, Remote, Internships, Scholarships)
- **Instant job lookup** with /jobs, /remote, /internships, /scholarships commands
- **Daily auto alerts** at 9 AM IST
- **Rich formatting** with Markdown support
- **Smart batching** to avoid message limits

### 👑 For Admins
- **/stats** - View comprehensive bot statistics
- **/broadcast** - Send messages to all users with confirmation
- **/confirm_broadcast** - Confirm and send broadcast messages
- **/cleanup_jobs** - Clean up old job listings
- **/confirm_cleanup** - Confirm and execute cleanup
- **Security controls** with admin-only access

### 🤖 Smart Features
- **Automatic scraping** from multiple job sources
- **Duplicate prevention** with intelligent job filtering
- **Rate limiting** to avoid Telegram API limits
- **Batch processing** for efficient message delivery
- **Webhook support** for production deployment
- **SQLite database** with proper indexing
- **Comprehensive logging** for monitoring and debugging

### 🛡️ Production Ready
- **Environment variable management** with validation
- **Error handling** throughout the application
- **Input validation** and sanitization
- **Health checks** and monitoring endpoints
- **CORS protection** and security headers
- **Database connection pooling** and management
- **Graceful shutdown** and startup procedures

---

## 🧠 Tech Stack

- **Python 3.10+** - Modern Python with type hints
- **python-telegram-bot 21.6** - Official Telegram bot library
- **FastAPI** - High-performance web framework
- **SQLite** - Lightweight database with proper indexing
- **APScheduler** - Advanced job scheduling
- **Requests** - HTTP client for scraping
- **python-dotenv** - Environment variable management
- **Uvicorn** - ASGI server for production

---

## ⚙️ Setup & Configuration

### 1. Environment Setup

#### Create Environment File
```bash
cp .env.example .env
```

#### Configure Environment Variables
Edit `.env` file with your settings:

```bash
# Required Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here
WEBHOOK_BASE_URL=https://your-app-name.onrender.com
WEBHOOK_TOKEN=your_webhook_token_here

# Optional Configuration
TIMEZONE=Asia/Kolkata
SCRAPE_INTERVAL_HOURS=3
DAILY_ALERT_HOUR=9
SEND_BATCH_SIZE=25
SEND_BATCH_SLEEP=0.6
LOG_LEVEL=INFO
DB_FILE=database.db
```

### 2. Local Development

#### Using Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f job-alert-bot
```

### 3. Production Deployment

#### Deploy to Render (Recommended)
1. **Fork this repository**
2. **Sign up for Render** at [render.com](https://render.com)
3. **Connect your repository** to Render
4. **Use the render.yaml** configuration file for automatic setup
5. **Set environment variables** in Render dashboard:
   - `TELEGRAM_TOKEN` - Your bot token from @BotFather
   - `ADMIN_ID` - Your Telegram user ID
   - `WEBHOOK_TOKEN` - Generate a secure token
6. **Deploy!** Render will automatically build and deploy your bot

#### Deploy to Railway
1. **Click the Railway deploy button**
2. **Fork and connect** your repository
3. **Set environment variables** in Railway dashboard
4. **Deploy your application**

#### Deploy to Heroku
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create new app
heroku create your-app-name

# Set environment variables
heroku config:set TELEGRAM_TOKEN=your_token
heroku config:set ADMIN_ID=your_id
heroku config:set WEBHOOK_TOKEN=your_token

# Deploy
git push heroku main

# Scale dyno
heroku ps:scale web=1
```

### 4. Bot Configuration

#### Set Up Webhook
Once deployed, set up the webhook with Telegram:
```bash
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-name.onrender.com/webhook/{YOUR_WEBHOOK_TOKEN}"}'
```

#### Verify Webhook
```bash
curl "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getWebhookInfo"
```

---

## 📊 Monitoring & Health Checks

### Health Check Endpoints
- **Basic Health**: `GET /` - Simple health check
- **Detailed Health**: `GET /api/health/detailed` - Comprehensive system status
- **Statistics**: `GET /api/stats` - Application statistics

### Monitoring Features
- **Uptime tracking** with startup time monitoring
- **Database connection** health checks
- **Bot status** verification
- **Webhook configuration** validation
- **Job processing** statistics
- **User engagement** metrics

---

## 🔧 Development

### Adding New Job Sources
1. **Create scraper function** in `services/scraper_engine.py`
2. **Add to run_scrapers()** function
3. **Test locally** before deploying
4. **Monitor logs** for any issues

### Customizing Job Categories
1. **Update category lists** in handlers
2. **Modify database schema** if needed
3. **Update admin commands** for new categories
4. **Test user experience** thoroughly

### Database Migrations
For database schema changes:
1. **Create backup** of existing data
2. **Update models** in `database/models.py`
3. **Add migration logic** in `database/db.py`
4. **Test migration** process

---

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Responding
- Check webhook configuration
- Verify environment variables
- Check application logs
- Ensure bot is not blocked by users

#### Database Issues
- Check file permissions
- Verify database path
- Monitor disk space
- Check for corruption

#### Scraping Failures
- Check network connectivity
- Verify API endpoints
- Monitor rate limits
- Check user-agent headers

### Log Analysis
```bash
# View application logs
docker-compose logs job-alert-bot

# Filter for errors
docker-compose logs job-alert-bot | grep ERROR

# Monitor in real-time
docker-compose logs -f job-alert-bot
```

### Performance Optimization
- **Adjust batch sizes** for message sending
- **Optimize database queries** with proper indexing
- **Monitor memory usage** and adjust accordingly
- **Scale horizontally** if needed

---

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **python-telegram-bot** team for the excellent library
- **FastAPI** team for the amazing web framework
- **All contributors** who help improve this project

---

## 📞 Support

For support and questions:
- **Create an Issue** on GitHub
- **Join our Discord** (if available)
- **Email**: support@example.com

---

**Made with ❤️ for the developer community**
- /stats

### Smart
- automatic scraping
- duplicate prevention
- batching (anti rate limit)
- webhook (Render free-tier safe)
- SQLite database
- async fast delivery

---

## 🧠 Tech Stack

- Python
- python-telegram-bot
- FastAPI
- SQLite
- Render hosting

---

## ⚙️ Setup

### 1. Install
