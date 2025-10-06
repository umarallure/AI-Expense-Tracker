# AI-Powered Expense Tracker - Backend API

FastAPI-based backend for the AI-Powered Expense Tracker system. This API provides intelligent document processing, transaction management, and financial analytics using Supabase and AI/LLM integration.

## 🚀 Features

### Phase 1 (✅ Completed)
- ✅ **Authentication System**: Supabase Auth integration with JWT tokens
- ✅ **Business Management**: Multi-business support with role-based access
- ✅ **User Management**: User profiles and team member management
- ✅ **Security**: Row-level security (RLS) policies and permission system
- ✅ **Comprehensive API Documentation**: Interactive Swagger UI and ReDoc
- ✅ **Logging & Monitoring**: Structured logging with request tracking

### Upcoming Phases
- 📄 **Document Processing**: AI-powered extraction from PDFs, images, and spreadsheets
- 💰 **Transaction Management**: Smart categorization and duplicate detection
- 🔧 **Custom Rule Engine**: Automated transaction processing rules
- 📊 **Analytics & Reporting**: Financial insights and tax reports
- 🔍 **Vector Search**: Semantic search across documents using pgvector

## 📋 Prerequisites

- Python 3.11+
- Supabase account and project
- OpenRouter API key (for Cohere access)
- (Optional) Cohere API key for direct access
- (Optional) n8n instance for workflow automation

## 🛠️ Installation

### 1. Navigate to backend directory

```bash
cd ai-powered-expense-tracker/backend
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required: Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Required: Security
SECRET_KEY=your-generated-secret-key-min-32-chars

# Required: AI Configuration
OPENROUTER_API_KEY=your-openrouter-key
COHERE_API_KEY=your-cohere-key
```

**Generate a secure SECRET_KEY:**
```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize Supabase database

Run the migration in Supabase SQL Editor:

1. Open your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy contents of `app/db/migrations/001_initial_schema.sql`
4. Paste and execute

Or use Supabase CLI:
```bash
supabase link --project-ref your-project-ref
supabase db push
```

## 🚀 Running the Application

### Development Mode (with hot reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
docker build -t expense-tracker-api .
docker run -p 8000:8000 --env-file .env expense-tracker-api
```

## 📚 API Documentation

Once running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔑 Quick Start - Authentication

### 1. Register a new user

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

### 3. Use token in requests

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer your-access-token"
```

## 🏢 Business Management

### Create a business

```bash
curl -X POST "http://localhost:8000/api/v1/businesses/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Acme Corp",
    "business_type": "llc",
    "currency": "USD",
    "industry": "Technology",
    "fiscal_year_start": 1
  }'
```

### List your businesses

```bash
curl -X GET "http://localhost:8000/api/v1/businesses/" \
  -H "Authorization: Bearer <token>"
```

## 🔐 Role-Based Access Control

Hierarchical permission system:

| Role | Create | Read | Update | Delete | Manage Members |
|------|--------|------|--------|--------|----------------|
| **Owner** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Accountant** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Viewer** | ❌ | ✅ | ❌ | ❌ | ❌ |

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── api.py                  # API router
│   │   └── endpoints/
│   │       ├── auth.py             # ✅ Authentication
│   │       ├── businesses.py       # ✅ Business management
│   │       ├── transactions.py     # 🔜 Transactions (Phase 4)
│   │       ├── documents.py        # 🔜 Documents (Phase 3)
│   │       ├── rules.py            # 🔜 Rules (Phase 5)
│   │       └── reports.py          # 🔜 Reports (Phase 6)
│   ├── core/
│   │   ├── config.py              # ✅ Settings & configuration
│   │   ├── security.py            # ✅ JWT, hashing, auth
│   │   └── deps.py                # ✅ Dependencies
│   ├── db/
│   │   ├── supabase.py            # ✅ Supabase client
│   │   └── migrations/
│   │       └── 001_initial_schema.sql  # ✅ Database schema
│   ├── models/                     # Database models (ORM)
│   ├── schemas/
│   │   ├── auth.py                # ✅ Auth schemas
│   │   └── business.py            # ✅ Business schemas
│   ├── services/                   # Business logic
│   │   ├── ai_extractor.py        # 🔜 AI extraction
│   │   ├── rule_engine.py         # 🔜 Rule processing
│   │   ├── report_generator.py    # 🔜 Report generation
│   │   └── embeddings.py          # 🔜 Vector embeddings
│   └── main.py                    # ✅ FastAPI app
├── tests/                          # Test suite
├── requirements.txt               # ✅ Dependencies
├── .env.example                   # ✅ Environment template
├── Dockerfile                     # Docker config
└── README.md                      # ✅ Documentation
```

## 🧪 Testing

Run tests:

```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test
pytest tests/test_auth.py -v
```

## 🔧 Development Tools

### Code Formatting

```bash
black app/          # Format code
isort app/          # Sort imports
flake8 app/         # Lint code
mypy app/           # Type checking
```

## 🐳 Docker

Build and run:

```bash
docker build -t expense-tracker-api .
docker run -p 8000:8000 --env-file .env expense-tracker-api
```

Docker Compose:

```bash
docker-compose up -d
```

## 📊 Database Schema (Phase 1)

### Tables

#### `businesses`
- Core business/organization information
- Currency, timezone, fiscal year settings
- Address and contact details
- JSONB settings field for flexibility

#### `business_members`
- Multi-user access management
- Role-based permissions (owner, admin, accountant, viewer)
- Invitation and membership tracking
- Per-member custom permissions

### Row Level Security (RLS)

All tables have RLS policies ensuring:
- Users can only access businesses they're members of
- Role-based write permissions
- Owner-only deletion rights

## 🔒 Security Features

- ✅ JWT-based authentication
- ✅ Bcrypt password hashing
- ✅ Row Level Security (RLS) in database
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ Request logging
- ✅ Error handling
- 🔜 Rate limiting
- 🔜 API key management

## 📝 Logging

Structured logging with Loguru:

```python
from loguru import logger

logger.info("User action", user_id=user_id, action="login")
logger.error("Processing failed", error=str(e), document_id=doc_id)
```

Configure via environment:
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `LOG_FORMAT`: console, json

## 🗺️ Development Roadmap

- [x] **Phase 1**: Authentication & Business Management
- [ ] **Phase 2**: Account & Category Management
- [ ] **Phase 3**: Document Processing Pipeline
- [ ] **Phase 4**: Transaction Management
- [ ] **Phase 5**: Custom Rule Engine
- [ ] **Phase 6**: Analytics & Reporting
- [ ] **Phase 7**: Tax Management
- [ ] **Phase 8**: Search & Advanced Features

## 🤝 Contributing

1. Follow existing code style
2. Write tests for new features
3. Update documentation
4. Run linting and tests before committing

## 📄 License

See LICENSE file for details.

## 🆘 Support

- Documentation: `/docs` endpoint
- Issues: GitHub Issues
- Email: [Add support email]

## 🙏 Acknowledgments

Built with:
- **FastAPI** - Modern Python web framework
- **Supabase** - Backend-as-a-Service platform
- **Cohere** - AI/LLM capabilities
- **Pydantic** - Data validation
- **Loguru** - Elegant logging