# AI-Powered Income and Expense Tracker

## Project Overview
The AI-Powered Expense Tracker is a comprehensive application designed to help users manage their financial transactions efficiently. It leverages AI technology to extract transaction data from various financial documents, apply custom business rules, and generate insightful reports. The application consists of a FastAPI backend integrated with a Supabase database and a React frontend utilizing Shadcn UI for a modern user experience.

## Features
- **User Authentication**: Secure user registration, login, and logout functionalities.
- **Business Management**: Create, update, and manage business profiles.
- **Transaction Management**: CRUD operations for transactions, including categorization and reconciliation.
- **Document Management**: Upload and process financial documents to extract transaction data.
- **Custom Rule Engine**: Define and apply custom rules to automate transaction categorization.
- **Reporting**: Generate various financial reports, including income statements and tax summaries.
- **AI Integration**: Utilize AI for data extraction and insights generation.

## Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL + pgvector)
- **AI/LLM**: Cohere via OpenRouter API
- **Workflow Orchestration**: n8n
- **Storage**: Supabase Storage
- **Frontend**: React 18+ with TypeScript
- **UI Library**: Shadcn UI + Tailwind CSS

## Project Structure
```
ai-powered-expense-tracker
├── backend
│   ├── app
│   │   ├── api
│   │   │   ├── v1
│   │   │   │   ├── endpoints
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── businesses.py
│   │   │   │   │   ├── transactions.py
│   │   │   │   │   ├── documents.py
│   │   │   │   │   ├── rules.py
│   │   │   │   │   └── reports.py
│   │   │   │   └── api.py
│   │   ├── core
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models
│   │   │   ├── transaction.py
│   │   │   ├── document.py
│   │   │   └── business.py
│   │   ├── schemas
│   │   │   ├── transaction.py
│   │   │   └── document.py
│   │   ├── services
│   │   │   ├── ai_extractor.py
│   │   │   ├── rule_engine.py
│   │   │   ├── report_generator.py
│   │   │   └── embeddings.py
│   │   ├── db
│   │   │   ├── supabase.py
│   │   │   └── migrations
│   │   └── main.py
│   ├── tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend
│   ├── src
│   │   ├── components
│   │   │   ├── ui
│   │   │   ├── auth
│   │   │   ├── dashboard
│   │   │   ├── transactions
│   │   │   ├── documents
│   │   │   ├── rules
│   │   │   └── reports
│   │   ├── lib
│   │   │   ├── supabase.ts
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   ├── hooks
│   │   ├── types
│   │   ├── pages
│   │   └── App.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── README.md
└── README.md
```

## Deployment

### Render Deployment
This application is configured for easy deployment on Render using the included `render.yaml` file.

#### Prerequisites
- A Render account
- A Supabase project with all required tables and configurations

#### Deployment Steps
1. **Connect to GitHub**: Link your Render account to the GitHub repository containing this code.

2. **Create New Blueprint**: In Render dashboard, click "New +" and select "Blueprint".

3. **Connect Repository**: Select your GitHub repository (`agenticfyai1-ai/AI-Expense-Tracker`).

4. **Configure Services**: Render will automatically detect the `render.yaml` file and create:
   - Backend API service (Python/FastAPI)
   - Frontend service (Static React app)

5. **Set Environment Variables**: Configure the following environment variables in Render:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret
   SECRET_KEY=generate_a_random_secret_key
   ENVIRONMENT=production
   DEBUG=false
   ```

6. **Deploy**: Click "Create Blueprint" and Render will build and deploy both services.

#### Post-Deployment
- The frontend will automatically connect to the backend API
- Access your application at the provided Render URLs
- Monitor logs and performance through the Render dashboard

### Environment Variables
Make sure to set these environment variables in your deployment platform:

**Backend:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key
- `SUPABASE_SERVICE_KEY`: Supabase service role key (for admin operations)
- `SUPABASE_JWT_SECRET`: Supabase JWT secret
- `SECRET_KEY`: Random secret key for JWT tokens
- `ENVIRONMENT`: Set to "production"
- `DEBUG`: Set to "false"

**Frontend:**
- `VITE_API_BASE_URL`: Will be automatically set by Render to point to the backend service

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.