#!/bin/bash

# 🚀 Render Deployment Setup Script
# Run this locally before deploying to ensure everything is ready

echo "🚀 AI-Powered Expense Tracker - Render Deployment Setup"
echo "======================================================"

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "✅ Project structure verified"

# Check backend requirements
echo ""
echo "📦 Checking backend dependencies..."
if [ -f "backend/requirements.txt" ]; then
    echo "✅ backend/requirements.txt found"
else
    echo "❌ backend/requirements.txt missing"
    exit 1
fi

# Check frontend package.json
echo ""
echo "📦 Checking frontend dependencies..."
if [ -f "frontend/package.json" ]; then
    echo "✅ frontend/package.json found"
else
    echo "❌ frontend/package.json missing"
    exit 1
fi

# Check render.yaml
echo ""
echo "📋 Checking render.yaml configuration..."
if [ -f "render.yaml" ]; then
    echo "✅ render.yaml found"
else
    echo "❌ render.yaml missing"
    exit 1
fi

# Check environment files
echo ""
echo "🔐 Checking environment configuration..."
if [ -f "backend/.env" ]; then
    echo "✅ backend/.env found"
    echo "⚠️  Please ensure production values are set in Render dashboard"
else
    echo "⚠️  backend/.env not found - configure in Render dashboard"
fi

# Check Git status
echo ""
echo "📝 Checking Git status..."
if git status --porcelain | grep -q .; then
    echo "⚠️  You have uncommitted changes. Please commit before deploying:"
    echo "   git add ."
    echo "   git commit -m 'Prepare for deployment'"
    echo "   git push origin main"
else
    echo "✅ Git repository is clean"
fi

# Check if remote is set
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Git remote 'origin' is configured"
    REMOTE_URL=$(git remote get-url origin)
    echo "   Remote: $REMOTE_URL"
else
    echo "❌ Git remote 'origin' not configured"
    exit 1
fi

echo ""
echo "🎯 Deployment Checklist:"
echo "========================"
echo ""
echo "Pre-deployment:"
echo "1. ✅ Project structure verified"
echo "2. ✅ Dependencies configured"
echo "3. ✅ render.yaml ready"
echo "4. ⏳ Environment variables (set in Render dashboard)"
echo "5. ⏳ Supabase project configured"
echo "6. ⏳ AI API keys configured"
echo ""
echo "Deployment Steps:"
echo "1. Go to https://render.com"
echo "2. Click 'New +' → 'Blueprint'"
echo "3. Connect your GitHub repository"
echo "4. Select this repository"
echo "5. Set environment variables in each service"
echo "6. Click 'Create Blueprint'"
echo "7. Wait for deployment (10-15 minutes)"
echo "8. Update frontend VITE_API_BASE_URL after backend deploys"
echo "9. Test the application"
echo ""
echo "🔗 Useful Links:"
echo "- Render Dashboard: https://dashboard.render.com"
echo "- Supabase Dashboard: https://supabase.com/dashboard"
echo "- OpenRouter API Keys: https://openrouter.ai/keys"
echo ""
echo "📚 Full Guide: See RENDER_DEPLOYMENT_GUIDE.md"
echo ""
echo "🎉 Ready for deployment!"