# kitchen-tracker - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
# Use the root package.json for convenience
npm run setup

# Or manually:
# cd frontend && npm install
# cd ../backend && pip install -r src/kitchen_tracker/requirements.txt
```

### 2. Development
```bash
# Frontend dev server
npm run dev:frontend

# Backend local API (in separate terminal)
npm run dev:backend

# Or manually:
# cd frontend && npm run dev
# cd backend && sam local start-api
```

### 3. Testing
```bash
# Run all tests
npm test

# Or individually:
npm run test:frontend  # Vue/Vitest tests
npm run test:backend   # Python/pytest tests
```

### 4. Deploy
```bash
# Development environment
npm run deploy:dev

# Production environment  
npm run deploy:prod

# Or manually:
# cd backend && sam deploy --config-env dev|prod
```

## Project Structure
- `package.json` - Root scripts for project management
- `frontend/` - Vue.js 3 + TypeScript application with full tooling
- `backend/` - Python Lambda functions with SAM
- Complete TypeScript, ESLint, and testing configuration
- Environment-based deployment ready

## What's Included
✅ **Frontend Tooling**: TypeScript, ESLint, Vitest, Vite  
✅ **Backend Configuration**: SAM, pytest, environment configs  
✅ **Authentication**: Cognito + JWT middleware ready  
✅ **Database**: DynamoDB tables configured  
✅ **Deployment**: Multi-environment SAM config  
✅ **Development**: Hot reload, local API, testing  

## Next Steps
1. Customize the data models in `backend/src/kitchen_tracker/models/`
2. Add your business logic to `backend/src/kitchen_tracker/app.py`
3. Create your Vue components in `frontend/src/components/`
4. Update the API service in `frontend/src/services/api.ts`
5. Configure your API URLs in `.env.development` and `.env.production`

This is a complete foundation with all tooling - focus on building your features!
