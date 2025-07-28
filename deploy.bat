@echo off
echo 🚀 Adcellerant Social Caption Generator - Deployment Helper
echo ==========================================================

:menu
echo.
echo Choose deployment option:
echo 1^) 🧪 Test locally
echo 2^) ☁️  Deploy to Streamlit Community Cloud (FREE)
echo 3^) 🟣 Deploy to Heroku  
echo 4^) 🔧 Show environment setup guide
echo 5^) 📦 Prepare files only (no deployment)
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto test_local
if "%choice%"=="2" goto deploy_streamlit
if "%choice%"=="3" goto deploy_heroku
if "%choice%"=="4" goto show_env_setup
if "%choice%"=="5" goto prepare_files
echo ❌ Invalid choice. Please try again.
goto menu

:test_local
echo 🧪 Testing local deployment...
if not exist ".env" (
    echo ❌ .env file not found! Creating template...
    echo OPENAI_API_KEY=your_openai_key_here > .env
    echo APP_PASSWORD=Jax2021 >> .env
    echo 📝 Please edit .env file with your actual OpenAI API key
    pause
    exit /b
)
echo Starting local server...
streamlit run social_post_generator.py --server.port 8501
goto end

:deploy_streamlit
echo ☁️  Deploying to Streamlit Community Cloud...
call :prepare_deployment
echo.
echo 1. Push your code to GitHub:
echo    git remote add origin https://github.com/USERNAME/REPOSITORY.git
echo    git push -u origin main
echo.
echo 2. Visit: https://share.streamlit.io
echo 3. Connect your GitHub account
echo 4. Select your repository
echo 5. Add environment variables:
echo    - OPENAI_API_KEY: [Your OpenAI API Key]
echo    - APP_PASSWORD: Jax2021
echo.
echo Your app will be available at:
echo https://USERNAME-REPOSITORY-main.streamlit.app
goto end

:deploy_heroku
echo 🟣 Deploying to Heroku...
where heroku >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Heroku CLI not found. Please install it first:
    echo    https://devcenter.heroku.com/articles/heroku-cli
    pause
    exit /b
)

call :prepare_deployment

set /p app_name="Enter your Heroku app name: "
set /p openai_key="Enter your OpenAI API key: "

echo Creating Heroku app...
heroku create %app_name%

echo Setting environment variables...
heroku config:set OPENAI_API_KEY="%openai_key%" --app %app_name%
heroku config:set APP_PASSWORD="Jax2021" --app %app_name%

echo Deploying to Heroku...
git push heroku main

echo ✅ Deployment complete!
echo Your app is available at: https://%app_name%.herokuapp.com
goto end

:show_env_setup
echo 🔧 Environment Variables Setup
echo =============================
echo.
echo Make sure to set these environment variables on your hosting platform:
echo.
echo OPENAI_API_KEY = [Your OpenAI API Key]
echo APP_PASSWORD = Jax2021
echo.
echo ⚠️  NEVER commit your .env file to GitHub!
echo ⚠️  Always use environment variables on hosting platforms!
goto end

:prepare_files
call :prepare_deployment
echo ✅ Files prepared for deployment!
goto end

:prepare_deployment
echo 📦 Preparing files for deployment...

if not exist ".git" (
    echo ⚠️  Git not initialized. Initializing now...
    git init
    git branch -M main
)

if not exist ".gitignore" (
    echo Creating .gitignore file...
    echo .env > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pyc >> .gitignore
    echo .streamlit/ >> .gitignore
    echo company_profiles.json >> .gitignore
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found! Please create it first.
    pause
    exit /b
)

git add .
git add -f Procfile setup.sh app.json

set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Deploy Adcellerant Social Caption Generator

git commit -m "%commit_msg%"
exit /b

:end
echo.
echo 🎉 Deployment process complete!
echo.
echo 📚 For more deployment options, check PASSWORD_SETUP.md
echo 🔐 Your app is password protected with: Jax2021
echo 📞 Need help? Check the troubleshooting section in the documentation
echo.
pause
