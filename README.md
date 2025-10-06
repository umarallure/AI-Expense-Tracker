# AI-Powered Expense Tracker

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

## Getting Started
To get started with the AI-Powered Expense Tracker, follow the instructions below:

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- Supabase account for database setup

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai-powered-expense-tracker
   ```

2. Set up the backend:
   - Navigate to the `backend` directory.
   - Install dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Configure your Supabase credentials in the `.env` file.

3. Set up the frontend:
   - Navigate to the `frontend` directory.
   - Install dependencies:
     ```
     npm install
     ```

### Running the Application
- Start the backend server:
  ```
  uvicorn app.main:app --reload
  ```

- Start the frontend development server:
  ```
  npm start
  ```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.