# Render Deployment Guide for Job Alert Bot

## Overview
This guide provides step-by-step instructions for deploying the Job Alert Bot on Render.

## Prerequisites
1. A Render account (https://render.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Telegram Bot Token from @BotFather
4. Your Telegram User ID (get it from @userinfobot)

## Step 1: Environment Variables

Set the following environment variables in your Render dashboard:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Your bot token from @BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_ID` | Your Telegram user ID | `123456789` |
| `WEBHOOK_BASE_URL` | Your Render service URL | `https://job-alert-bot.onrender.com` |
| `WEBHOOK_TOKEN` | Random secret token for webhook security | `your_random_secret_token_here` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TIMEZONE` | Timezone for scheduling | `Asia/Kolkata` |
| `SCRAPE_INTERVAL_HOURS` | Hours between scrapes | `3` |
| `DAILY_ALERT_HOUR` | Hour for daily alerts (24h format) | `9` |
| `SEND_BATCH_SIZE` | Users per notification batch | `25` |
| `SEND_BATCH_SLEEP` | Delay between messages (seconds) | `0.6` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DB_FILE` | Database file path | `database.db` |

## Step 2: Render Configuration

Your `render.yaml` is already configured. Here's what it does:

```yaml
services:
  - type: web
    name: job-alert-bot
    env: python
    region: oregon
    plan: free
    runtime: python3.13
    buildCommand: pip install -r requirements.txt
    startCommand: "uvicorn asgi:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info"
    healthCheckPath: /
    envVars:
      - key: TELEGRAM_TOKEN
        sync: false
      - key: ADMIN_ID
        sync: false
      - key: WEBHOOK_BASE_URL
        fromService: true
        service: job-alert-bot
      - key: WEBHOOK_TOKEN
        sync: false
      # ... other env vars
```

## Step 3: Deployment Steps

### Method 1: Using Render Dashboard (Recommended)

1. **Create New Web Service**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Service**
   - Name: `job-alert-bot` (or your preferred name)
   - Region: Choose closest to your users
   - Branch: `main` (or your default branch)
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn asgi:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info`

3. **Set Environment Variables**
   - Go to "Environment" tab
   - Add all required variables listed above
   - For `WEBHOOK_BASE_URL`, use your service URL (e.g., `https://job-alert-bot.onrender.com`)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

### Method 2: Using Render Blueprint (render.yaml)

1. Push your code including `render.yaml` to your repository
2. Go to https://dashboard.render.com/blueprints
3. Click "New Blueprint Instance"
4. Connect your repository
5. Render will automatically detect `render.yaml` and configure the service

## Step 4: Verify Deployment

1. **Check Health Endpoint**
   ```
   https://your-service-url.onrender.com/
   ```
   Should return JSON with status "healthy"

2. **Check Stats Endpoint**
   ```
   https://your-service-url.onrender.com/api/stats
   ```
   Should return bot and database statistics

3. **Test Bot**
   - Open Telegram
   - Find your bot
   - Send `/start` command
   - Bot should respond with welcome message

## Step 5: Webhook Configuration

The bot automatically sets up the webhook on startup. The webhook URL will be:
```
https://your-service-url.onrender.com/webhook/YOUR_WEBHOOK_TOKEN
```

## Troubleshooting

### Issue: "No JobQueue set up" Warning
**Solution**: This is now fixed. The `requirements.txt` includes `python-telegram-bot[job-queue]` which installs the required dependencies.

### Issue: "NoneType object has no attribute 'run_repeating'"
**Solution**: Fixed in the updated scheduler. The bot now uses a fallback mechanism if JobQueue is not available.

### Issue: Bot not responding
1. Check logs in Render dashboard
2. Verify `TELEGRAM_TOKEN` is correct
3. Ensure webhook URL is accessible
4. Check that `WEBHOOK_TOKEN` matches

### Issue: Database errors
1. On Render free tier, the filesystem is ephemeral
2. Consider using Render's PostgreSQL for persistent storage
3. Or implement a backup strategy

### Issue: Scrapers not working
1. Check logs for specific scraper errors
2. Some sites may block Render's IP addresses
3. Consider using proxy services for production

## Important Notes

### Free Tier Limitations
- **Sleeping**: Free web services sleep after 15 minutes of inactivity
- **Cold Start**: First request after sleep may take 30+ seconds
- **Disk**: Filesystem is ephemeral (resets on each deploy)

### Recommendations
1. **Upgrade to Paid Plan** for production use
2. **Use External Database** (PostgreSQL) for persistence
3. **Set Up Monitoring** using Render's built-in metrics
4. **Configure Alerts** for service downtime

## Bot Commands

User Commands:
- `/start` - Register and choose category
- `/jobs` - Get latest job listings
- `/remote` - Get remote job listings
- `/internships` - Get internship listings
- `/scholarships` - Get scholarship listings

Admin Commands:
- `/stats` - View bot statistics
- `/broadcast <message>` - Send message to all users
- `/confirm_broadcast` - Confirm broadcast
- `/cleanup_jobs [days]` - Clean old jobs (default 30 days)
- `/confirm_cleanup` - Confirm cleanup

## Monitoring

Check these endpoints:
- `GET /` - Health check
- `GET /api/stats` - Detailed statistics
- `GET /api/health/detailed` - System health details

## Support

For issues:
1. Check Render logs first
2. Verify all environment variables
3. Test locally before deploying
4. Check Telegram Bot API status
