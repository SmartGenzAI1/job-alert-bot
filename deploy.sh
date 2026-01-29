#!/bin/bash

# Job Alert Bot Deployment Script
# Production-ready deployment for Render, Heroku, or Docker

set -e  # Exit on any error

echo "🚀 Job Alert Bot Deployment Script"
echo "=================================="

# Check if required environment variables are set
check_env_vars() {
    echo "🔍 Checking environment variables..."
    
    if [ -z "$TELEGRAM_TOKEN" ]; then
        echo "❌ Error: TELEGRAM_TOKEN not set"
        echo "Please set: export TELEGRAM_TOKEN=your_bot_token"
        exit 1
    fi
    
    if [ -z "$ADMIN_ID" ]; then
        echo "❌ Error: ADMIN_ID not set"
        echo "Please set: export ADMIN_ID=your_telegram_user_id"
        exit 1
    fi
    
    if [ -z "$WEBHOOK_TOKEN" ]; then
        echo "❌ Error: WEBHOOK_TOKEN not set"
        echo "Please set: export WEBHOOK_TOKEN=your_webhook_token"
        exit 1
    fi
    
    echo "✅ Environment variables check passed"
}

# Validate webhook URL
validate_webhook_url() {
    if [ -z "$WEBHOOK_BASE_URL" ]; then
        echo "⚠️  Warning: WEBHOOK_BASE_URL not set"
        echo "Using default: https://localhost:8000"
        export WEBHOOK_BASE_URL="https://localhost:8000"
    fi
    echo "✅ Webhook URL: $WEBHOOK_BASE_URL"
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
}

# Initialize database
init_database() {
    echo "🗄️  Initializing database..."
    python -c "
import sys
sys.path.insert(0, '.')
from database.db import init_db
init_db()
print('✅ Database initialized')
"
}

# Set up webhook
setup_webhook() {
    echo "🌐 Setting up Telegram webhook..."
    
    if [ -n "$WEBHOOK_BASE_URL" ] && [ -n "$WEBHOOK_TOKEN" ]; then
        WEBHOOK_URL="$WEBHOOK_BASE_URL/webhook/$WEBHOOK_TOKEN"
        echo "Setting webhook to: $WEBHOOK_URL"
        
        curl -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook" \
            -H "Content-Type: application/json" \
            -d "{\"url\": \"$WEBHOOK_URL\"}" \
            --fail
            
        echo "✅ Webhook configured"
    else
        echo "⚠️  Skipping webhook setup (missing environment variables)"
    fi
}

# Verify deployment
verify_deployment() {
    echo "🔍 Verifying deployment..."
    
    # Check if main.py can be imported
    python -c "
import sys
sys.path.insert(0, '.')
try:
    import main
    print('✅ Main application imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    # Check if bot can be created
    python -c "
import sys
sys.path.insert(0, '.')
try:
    from bot import create_bot
    print('✅ Bot creation successful')
except Exception as e:
    print(f'❌ Bot creation error: {e}')
    sys.exit(1)
"
    
    echo "✅ Deployment verification passed"
}

# Start the application
start_application() {
    echo "🚀 Starting application..."
    
    if [ "$1" = "dev" ]; then
        echo "Starting in development mode..."
        uvicorn app:app --reload --host 0.0.0.0 --port 8000
    else
        echo "Starting in production mode..."
        uvicorn app:app --host 0.0.0.0 --port 8000
    fi
}

# Docker deployment
deploy_docker() {
    echo "🐳 Building Docker image..."
    docker build -t job-alert-bot .
    
    echo "🐳 Running Docker container..."
    docker run -d \
        --name job-alert-bot \
        -p 8000:8000 \
        -e TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
        -e ADMIN_ID="$ADMIN_ID" \
        -e WEBHOOK_BASE_URL="$WEBHOOK_BASE_URL" \
        -e WEBHOOK_TOKEN="$WEBHOOK_TOKEN" \
        job-alert-bot
    
    echo "✅ Docker deployment complete"
    echo "Container logs: docker logs -f job-alert-bot"
}

# Health check
health_check() {
    echo "🏥 Running health check..."
    
    sleep 5  # Wait for server to start
    
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Health check passed"
        curl http://localhost:8000/api/stats
    else
        echo "❌ Health check failed"
        echo "Check application logs for errors"
        return 1
    fi
}

# Show deployment instructions
show_instructions() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Verify your bot is running at: http://localhost:8000"
    echo "2. Check health status: curl http://localhost:8000/"
    echo "3. View statistics: curl http://localhost:8000/api/stats"
    echo ""
    echo "🔧 For Production Deployment:"
    echo "- Use Render: https://render.com (free tier)"
    echo "- Use Heroku: https://heroku.com"
    echo "- Use Docker: docker-compose up -d"
    echo ""
    echo "⚠️  Important Security Notes:"
    echo "- Never commit .env file to version control"
    echo "- Use strong webhook tokens (32+ characters)"
    echo "- Monitor logs for errors and security issues"
    echo "- Keep dependencies updated"
    echo ""
    echo "📚 Documentation:"
    echo "- Full README: https://github.com/SmartGenzAI1/job-alert-bot"
    echo "- Deployment guide in README.md"
    echo ""
}

# Main deployment function
main() {
    case "${1:-help}" in
        "check")
            check_env_vars
            validate_webhook_url
            ;;
        "install")
            check_env_vars
            install_dependencies
            init_database
            ;;
        "webhook")
            check_env_vars
            validate_webhook_url
            setup_webhook
            ;;
        "verify")
            verify_deployment
            ;;
        "dev")
            check_env_vars
            validate_webhook_url
            install_dependencies
            init_database
            setup_webhook
            verify_deployment
            start_application dev
            ;;
        "prod")
            check_env_vars
            validate_webhook_url
            install_dependencies
            init_database
            setup_webhook
            verify_deployment
            start_application prod
            ;;
        "docker")
            check_env_vars
            validate_webhook_url
            deploy_docker
            ;;
        "health")
            health_check
            ;;
        "full")
            check_env_vars
            validate_webhook_url
            install_dependencies
            init_database
            setup_webhook
            verify_deployment
            health_check
            show_instructions
            ;;
        "help"|*)
            echo "Job Alert Bot Deployment Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  check     - Check environment variables"
            echo "  install   - Install dependencies and init database"
            echo "  webhook   - Set up Telegram webhook"
            echo "  verify    - Verify deployment readiness"
            echo "  dev       - Start in development mode"
            echo "  prod      - Start in production mode"
            echo "  docker    - Deploy using Docker"
            echo "  health    - Run health check"
            echo "  full      - Complete deployment (recommended)"
            echo "  help      - Show this help message"
            echo ""
            echo "Environment Variables Required:"
            echo "  TELEGRAM_TOKEN    - Your bot token from @BotFather"
            echo "  ADMIN_ID        - Your Telegram user ID"
            echo "  WEBHOOK_TOKEN   - Secure token for webhooks"
            echo "  WEBHOOK_BASE_URL - Your deployment URL (optional)"
            ;;
    esac
}

# Run main function with all arguments
main "$@"