# Daily Logger Assist

An intelligent daily work tracking system that automates JIRA status updates by parsing Teams messages and emails, extracting work information using AI, and providing comprehensive 8-hour daily work distribution.

## 🎯 Project Status

### ✅ **Phase 1: Foundation (COMPLETED)**
- FastAPI setup with authentication
- Database models and relationships  
- API endpoints and documentation
- JWT token authentication
- Environment setup and dependencies

### ✅ **Phase 2: Data Collection (COMPLETED)**
- **Microsoft Teams Service**: Collect messages via Graph API
- **Email Service**: Collect emails via IMAP (Outlook/Exchange)
- **JIRA Service**: Sync tickets and manage work logs  
- **AI Service**: Content analysis using OpenRoute API
- **Background Tasks**: Celery workers for async processing
- **Updated API Endpoints**: Real background task integration

### 🚧 **Phase 3: AI Processing (PENDING)**
- Content analysis and work item extraction
- Task matching and time estimation
- Summary generation and insights

### 🚧 **Phase 4: Reporting (PENDING)**  
- Daily/weekly report generation
- JIRA work log updates
- Dashboard and analytics

### 🚧 **Phase 5: Testing & Deployment (PENDING)**
- Comprehensive testing suite
- Performance optimization
- Security hardening
- Production deployment

## 🚀 Quick Start

### Prerequisites
```bash
- Python 3.8+
- Redis server (for background tasks)
- OpenRoute API key (for AI features)
```

### Installation
```bash
git clone <repository>
cd DailyLoggerAssist
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Setup
Create `.env` file:
```env
SECRET_KEY=your-secret-key-change-in-production
OPENROUTE_API_KEY=your-openroute-api-key

# Microsoft Teams (optional)
TEAMS_CLIENT_ID=your-teams-client-id
TEAMS_CLIENT_SECRET=your-teams-secret
TEAMS_TENANT_ID=your-tenant-id

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Database Setup
```bash
python scripts/setup_db.py
```

### Start Services

**1. Start Redis (required for background tasks):**
```bash
redis-server
```

**2. Start FastAPI server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. Start Celery workers (optional for background tasks):**
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

**4. Start Celery beat for scheduled tasks (optional):**
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/teams/login` - Teams OAuth
- `POST /api/v1/auth/jira/login` - JIRA authentication
- `GET /api/v1/auth/status` - Check auth status

### Data Collection ✨ **NEW IN PHASE 2**
- `POST /api/v1/data/sync/teams?since_hours=24` - Collect Teams data
- `POST /api/v1/data/sync/email?since_hours=24` - Collect email data  
- `POST /api/v1/data/sync/jira?since_hours=24` - Sync JIRA tickets
- `POST /api/v1/data/process` - AI analysis of collected data
- `GET /api/v1/data/sync/status` - Check sync status

### Reports
- `GET /api/v1/reports/daily/{date}` - Get daily report
- `POST /api/v1/reports/generate` - Generate new report

### Admin
- `GET /api/v1/admin/system/status` - System health
- `GET /health` - Health check

## 🎛️ New Services (Phase 2)

### Teams Service
```python
from app.services.teams_service import TeamsService

service = TeamsService()
messages = await service.collect_messages(user, since_datetime)
```

### Email Service  
```python
from app.services.email_service import EmailService

service = EmailService()
emails = await service.collect_messages(user, since_datetime)
```

### JIRA Service
```python
from app.services.jira_service import JIRAService

service = JIRAService()
tickets = await service.get_user_tickets(user, since_datetime)
```

### AI Service
```python
from app.services.ai_service import AIService

service = AIService()
work_items = await service.analyze_content_for_work_items(content)
```

## 🔄 Background Tasks

### Data Collection Tasks
- `collect_teams_data` - Collect Teams messages
- `collect_email_data` - Collect email messages
- `collect_jira_data` - Sync JIRA tickets
- `collect_all_data` - Full data collection

### AI Processing Tasks
- `process_pending_analysis` - Analyze messages for work items
- `match_work_items_to_jira` - Match work to JIRA tickets
- `generate_daily_reports` - Create daily summaries

### Scheduled Tasks
- **Hourly**: Data collection from all sources
- **Every 30 min**: AI analysis processing
- **Daily**: Report generation

## 🧪 Testing

### Test Phase 2 Services
```bash
python scripts/test_phase2.py
```

### Manual API Testing
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "first_name": "Test", "last_name": "User"}'

# Check system status
curl http://localhost:8000/api/v1/admin/system/status
```

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI API    │    │   Background    │
│   (Future)      │◄──►│   - Auth         │◄──►│   - Celery      │
│                 │    │   - Data Mgmt    │    │   - Redis       │
└─────────────────┘    │   - Reports      │    │   - AI Tasks    │
                       └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Services       │    │   External      │
                       │   - Teams        │◄──►│   - MS Teams    │
                       │   - Email        │    │   - Email       │
                       │   - JIRA         │    │   - JIRA        │
                       │   - AI           │    │   - OpenRoute   │
                       └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   Database       │
                       │   - Users        │
                       │   - Messages     │
                       │   - Work Items   │
                       │   - JIRA Tickets │
                       │   - Reports      │
                       └──────────────────┘
```

## 🔑 Key Features Implemented

### ✅ Phase 1 Features
- JWT authentication with refresh tokens
- User management and credential storage
- Database models for all entities
- RESTful API with OpenAPI documentation
- Health monitoring and system status

### ✅ Phase 2 Features (NEW)
- **Real-time data collection** from Teams, Email, and JIRA
- **AI-powered content analysis** using OpenRoute
- **Background task processing** with Celery
- **Async service architecture** for scalability
- **Work item extraction** from communications
- **JIRA ticket matching** with AI
- **Daily report generation** with insights
- **Configurable sync intervals** and retry logic

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Authentication**: JWT tokens, OAuth 2.0
- **Background Tasks**: Celery, Redis
- **AI Integration**: OpenRoute API
- **External APIs**: Microsoft Graph, JIRA REST, IMAP
- **Testing**: pytest, async testing
- **Documentation**: OpenAPI/Swagger

## 🔮 Next Steps (Phase 3)

1. **Enhanced AI Processing**
   - Improved work item classification
   - Smart time estimation algorithms
   - Context-aware JIRA matching
   - Productivity insights and patterns

2. **Advanced Features**
   - Real-time dashboard
   - Custom report templates
   - Automated JIRA work logging
   - Team collaboration features

3. **Performance & Security**
   - Caching strategies
   - Rate limiting
   - Data encryption
   - Audit logging

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Current Status**: ✅ Phase 2 Complete - Data Collection & Background Tasks
**Last Updated**: $(date)
**Next Milestone**: Phase 3 - Advanced AI Processing 