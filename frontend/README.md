# AI-Powered Expense Tracker - Frontend Documentation

## Overview
This project is the frontend for the AI-Powered Expense Tracker application. It is built using React and integrates with a FastAPI backend and Supabase database to provide a seamless user experience for managing expenses, transactions, and financial reports.

## Technology Stack
- **Framework**: React 18+ with TypeScript
- **UI Library**: Shadcn UI + Tailwind CSS
- **State Management**: React Query + Zustand
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts
- **File Upload**: react-dropzone

## Project Structure
```
frontend
├── src
│   ├── components
│   │   ├── ui
│   │   ├── auth
│   │   ├── dashboard
│   │   ├── transactions
│   │   ├── documents
│   │   ├── rules
│   │   └── reports
│   ├── lib
│   │   ├── supabase.ts
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── hooks
│   ├── types
│   ├── pages
│   └── App.tsx
├── package.json
├── tailwind.config.js
└── README.md
```

## Getting Started
1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd ai-powered-expense-tracker/frontend
   ```

2. **Install dependencies**:
   ```
   npm install
   ```

3. **Run the application**:
   ```
   npm start
   ```

4. **Open your browser** and navigate to `http://localhost:3000` to view the application.

## Features
- User authentication (login, signup, password reset)
- Business and account management
- Document upload and processing
- Transaction management with CRUD operations
- Custom rule creation and application
- Financial analytics and reporting

## Contributing
Contributions are welcome! Please follow the standard Git workflow:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch and create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.