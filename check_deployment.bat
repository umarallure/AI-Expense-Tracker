@echo off
REM 🚀 Render Deployment Setup Script (Windows Batch)
REM Run this locally before deploying to ensure everything is ready

echo 🚀 AI-Powered Expense Tracker - Render Deployment Setup
echo ======================================================

REM Check if we're in the right directory
if not exist "backend" (
    echo ❌ Error: Please run this script from the project root directory
    pause
    exit /b 1
)
if not exist "frontend" (
    echo ❌ Error: Please run this script from the project root directory
    pause
    exit /b 1
)

echo ✅ Project structure verified

REM Check backend requirements
echo.
echo 📦 Checking backend dependencies...
if exist "backend\requirements.txt" (
    echo ✅ backend\requirements.txt found
) else (
    echo ❌ backend\requirements.txt missing
    pause
    exit /b 1
)

REM Check frontend package.json
echo.
echo 📦 Checking frontend dependencies...
if exist "frontend\package.json" (
    echo ✅ frontend\package.json found
) else (
    echo ❌ frontend\package.json missing
    pause
    exit /b 1
)

REM Check render.yaml
echo.
echo 📋 Checking render.yaml configuration...
if exist "render.yaml" (
    echo ✅ render.yaml found
) else (
    echo ❌ render.yaml missing
    pause
    exit /b 1
)

REM Check environment files
echo.
echo 🔐 Checking environment configuration...
if exist "backend\.env" (
    echo ✅ backend\.env found
    echo ⚠️  Please ensure production values are set in Render dashboard
) else (
    echo ⚠️  backend\.env not found - configure in Render dashboard
)

REM Check Git status
echo.
echo 📝 Checking Git status...
git status --porcelain >nul 2>&1
if %errorlevel% equ 0 (
    for /f %%i in ('git status --porcelain 2^>nul') do (
        echo ⚠️  You have uncommitted changes. Please commit before deploying:
        echo    git add .
        echo    git commit -m "Prepare for deployment"
        echo    git push origin main
        goto :git_check_done
    )
)
echo ✅ Git repository is clean
:git_check_done

REM Check if remote is set
echo.
echo 🔗 Checking Git remote...
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Git remote 'origin' is configured
    for /f "tokens=*" %%i in ('git remote get-url origin') do echo    Remote: %%i
) else (
    echo ❌ Git remote 'origin' not configured
    pause
    exit /b 1
)

echo.
echo 🎯 Deployment Checklist:
echo ========================
echo.
echo Pre-deployment:
echo 1. ✅ Project structure verified
echo 2. ✅ Dependencies configured
echo 3. ✅ render.yaml ready
echo 4. ⏳ Environment variables (set in Render dashboard)
echo 5. ⏳ Supabase project configured
echo 6. ⏳ AI API keys configured
echo.
echo Deployment Steps:
echo 1. Go to https://render.com
echo 2. Click New+ -^> Blueprint
echo 3. Connect your GitHub repository
echo 4. Select this repository
echo 5. Set environment variables in each service
echo 6. Click Create Blueprint
echo 7. Wait for deployment (10-15 minutes)
echo 8. Update frontend VITE_API_BASE_URL after backend deploys
echo 9. Test the application
echo.
echo 🔗 Useful Links:
echo - Render Dashboard: https://dashboard.render.com
echo - Supabase Dashboard: https://supabase.com/dashboard
echo - OpenRouter API Keys: https://openrouter.ai/keys
echo.
echo 📚 Full Guide: See RENDER_DEPLOYMENT_GUIDE.md
echo.
echo 🎉 Ready for deployment!
echo.
pause