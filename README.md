# Job Alert Bot 🤖

[![CI/CD](https://github.com/SmartGenzAI1/job-alert-bot/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/SmartGenzAI1/job-alert-bot/actions/workflows/ci-cd.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade Telegram bot for job alerts with multi-source scraping, intelligent scheduling, and robust error handling.

## 🌟 Features

- **Multi-Source Job Scraping**: RemoteOK, We Work Remotely, Remotive, and more
- **Intelligent Scheduling**: Automatic scraping with configurable intervals
- **Circuit Breaker Pattern**: Protects against cascading failures
- **Exponential Backoff**: Automatic retry with intelligent backoff
- **Structured Logging**: JSON logging with correlation IDs for request tracing
- **Input Validation**: Comprehensive validation and SQL injection prevention
- **Connection Pooling**: Thread-safe database operations with transaction management
- **Prometheus Metrics**: Monitoring and alerting support
- **Health Checks**: Comprehensive health check endpoints
- **Multi-Environment Config**: Support for dev/staging/production environments

## 🏗️ Architecture

```
job-alert-bot/
├── src/job_alert_bot/
│   ├── config/           # Configuration management
│   ├── database/         # Database models and connection pooling
│   ├── handlers/         # Telegram bot command handlers
│   ├── monitoring/       # Metrics and health checks
│   ├── services/         # Business logic (scrapers, scheduler, notifier)
│   └── utils/            # Utilities (validation, retry, circuit breaker)
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── .github/workflows/    # CI/CD pipelines
├── monitoring/           # Prometheus/Grafana configs
└── docs/                # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Your Telegram User ID (from [@userinfobot](https://t.me/userinfobot))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/SmartGenzAI1/job-alert-bot.git
cd job-alert-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the bot**
```bash
python -m src.job_alert_bot
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather | Yes | - |
| `ADMIN_ID` | Your Telegram user ID | Yes | - |
| `WEBHOOK_BASE_URL` | Webhook base URL | Yes | - |
| `WEBHOOK_TOKEN` | Webhook security token | Yes | - |
| `ENVIRONMENT` | Environment name | No | `development` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `DB_FILE` | Database file path | No | `database.db` |
| `SCRAPE_INTERVAL_HOURS` | Scraping interval | No | `3` |
| `DAILY_ALERT_HOUR` | Daily alert time | No | `9` |

See [`.env.example`](.env.example) for complete configuration options.

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run specific test categories
```bash
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration tests only
pytest tests/e2e          # End-to-end tests only
```

## 📊 Monitoring

### Health Check Endpoints

- `GET /` - Basic health check
- `GET /api/health/detailed` - Detailed health status
- `GET /api/stats` - Application statistics
- `GET /metrics` - Prometheus metrics

### Metrics

The bot exposes Prometheus metrics:

- `job_bot_requests_total` - Total HTTP requests
- `job_bot_scraper_jobs_added_total` - Jobs added by source
- `job_bot_scraper_errors_total` - Scraper errors
- `job_bot_messages_sent_total` - Messages sent
- `job_bot_circuit_breaker_state` - Circuit breaker states

## 🚀 Deployment

### Render (Recommended)

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set environment variables in Render dashboard
5. Deploy!

See [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md) for detailed instructions.

### Docker

```bash
# Build image
docker build -t job-alert-bot .

# Run container
docker run -d \
  -e TELEGRAM_TOKEN=your_token \
  -e ADMIN_ID=your_id \
  -e WEBHOOK_BASE_URL=your_url \
  -e WEBHOOK_TOKEN=your_token \
  -p 8000:8000 \
  job-alert-bot
```

## 📝 Bot Commands

### User Commands

- `/start` - Register and choose job category
- `/jobs` - Get latest job listings
- `/remote` - Get remote job listings
- `/internships` - Get internship listings
- `/scholarships` - Get scholarship listings

### Admin Commands

- `/stats` - View bot statistics
- `/broadcast <message>` - Send message to all users
- `/confirm_broadcast` - Confirm broadcast
- `/cleanup_jobs [days]` - Clean old jobs (default: 30 days)
- `/confirm_cleanup` - Confirm cleanup

## 🔒 Security

- Input validation and sanitization on all user inputs
- SQL injection prevention using parameterized queries
- HTML escaping to prevent XSS
- Circuit breaker pattern to prevent abuse
- Webhook token validation
- Rate limiting on message sending

## 🛠️ Development

### Code Style

We use Black, isort, and flake8 for code formatting:

```bash
# Format code
black src tests
isort src tests

# Lint code
flake8 src tests
mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install
```

## 📈 CI/CD

The project uses GitHub Actions for:

- **Linting**: flake8, black, isort, mypy
- **Testing**: pytest with coverage
- **Security**: Bandit, Safety
- **Building**: Docker image build and push
- **Deployment**: Automated deployment to staging/production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/process changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Prometheus](https://prometheus.io/) - Monitoring and alerting

## 📞 Support

For support, please:
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/SmartGenzAI1/job-alert-bot/issues)
3. Create a new issue if needed

---

Made with ❤️ by [SmartGenzAI](https://github.com/SmartGenzAI1)
