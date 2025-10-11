# 🚀 Render Deployment Setup Script (PowerShell)
# Run this locally before deploying to ensure everything is ready

Write-Host "🚀 AI-Powered Expense Tracker - Render Deployment Setup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (!(Test-Path "backend") -or !(Test-Path "frontend")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Project structure verified" -ForegroundColor Green

# Check backend requirements
Write-Host ""
Write-Host "📦 Checking backend dependencies..." -ForegroundColor Yellow
if (Test-Path "backend/requirements.txt") {
    Write-Host "✅ backend/requirements.txt found" -ForegroundColor Green
} else {
    Write-Host "❌ backend/requirements.txt missing" -ForegroundColor Red
    exit 1
}

# Check frontend package.json
Write-Host ""
Write-Host "📦 Checking frontend dependencies..." -ForegroundColor Yellow
if (Test-Path "frontend/package.json") {
    Write-Host "✅ frontend/package.json found" -ForegroundColor Green
} else {
    Write-Host "❌ frontend/package.json missing" -ForegroundColor Red
    exit 1
}

# Check render.yaml
Write-Host ""
Write-Host "📋 Checking render.yaml configuration..." -ForegroundColor Yellow
if (Test-Path "render.yaml") {
    Write-Host "✅ render.yaml found" -ForegroundColor Green
} else {
    Write-Host "❌ render.yaml missing" -ForegroundColor Red
    exit 1
}

# Check environment files
Write-Host ""
Write-Host "🔐 Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path "backend/.env") {
    Write-Host "✅ backend/.env found" -ForegroundColor Green
    Write-Host "⚠️  Please ensure production values are set in Render dashboard" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  backend/.env not found - configure in Render dashboard" -ForegroundColor Yellow
}

# Check Git status
Write-Host ""
Write-Host "📝 Checking Git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain 2>$null
if ($gitStatus) {
    Write-Host "⚠️  You have uncommitted changes. Please commit before deploying:" -ForegroundColor Yellow
    Write-Host "   git add ." -ForegroundColor White
    Write-Host "   git commit -m 'Prepare for deployment'" -ForegroundColor White
    Write-Host "   git push origin main" -ForegroundColor White
} else {
    Write-Host "✅ Git repository is clean" -ForegroundColor Green
}

# Check if remote is set
try {
    $remoteUrl = git remote get-url origin 2>$null
    if ($remoteUrl) {
        Write-Host "✅ Git remote 'origin' is configured" -ForegroundColor Green
        Write-Host "   Remote: $remoteUrl" -ForegroundColor White
    } else {
        Write-Host "❌ Git remote 'origin' not configured" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Git remote 'origin' not configured" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎯 Deployment Checklist:" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pre-deployment:" -ForegroundColor White
Write-Host "1. ✅ Project structure verified" -ForegroundColor Green
Write-Host "2. ✅ Dependencies configured" -ForegroundColor Green
Write-Host "3. ✅ render.yaml ready" -ForegroundColor Green
Write-Host "4. ⏳ Environment variables (set in Render dashboard)" -ForegroundColor Yellow
Write-Host "5. ⏳ Supabase project configured" -ForegroundColor Yellow
Write-Host "6. ⏳ AI API keys configured" -ForegroundColor Yellow
Write-Host ""
Write-Host "Deployment Steps:" -ForegroundColor White
Write-Host "1. Go to https://render.com" -ForegroundColor White
Write-Host "2. Click New+ -> Blueprint" -ForegroundColor White
Write-Host "3. Connect your GitHub repository" -ForegroundColor White
Write-Host "4. Select this repository" -ForegroundColor White
Write-Host "5. Set environment variables in each service" -ForegroundColor White
Write-Host "6. Click Create Blueprint" -ForegroundColor White
Write-Host "7. Wait for deployment (10-15 minutes)" -ForegroundColor White
Write-Host "8. Update frontend VITE_API_BASE_URL after backend deploys" -ForegroundColor White
Write-Host "9. Test the application" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Useful Links:" -ForegroundColor Cyan
Write-Host "- Render Dashboard: https://dashboard.render.com" -ForegroundColor White
Write-Host "- Supabase Dashboard: https://supabase.com/dashboard" -ForegroundColor White
Write-Host "- OpenRouter API Keys: https://openrouter.ai/keys" -ForegroundColor White
Write-Host ""
Write-Host "📚 Full Guide: See RENDER_DEPLOYMENT_GUIDE.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Ready for deployment!" -ForegroundColor Green