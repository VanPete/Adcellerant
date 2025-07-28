#!/bin/bash

# Adcellerant Social Caption Generator - Deployment Script
# This script helps deploy your app to various platforms

echo "🚀 Adcellerant Social Caption Generator - Deployment Helper"
echo "=========================================================="

# Function to check if git is initialized
check_git() {
    if [ ! -d ".git" ]; then
        echo "⚠️  Git not initialized. Initializing now..."
        git init
        git branch -M main
    fi
}

# Function to prepare for deployment
prepare_deployment() {
    echo "📦 Preparing files for deployment..."
    
    # Ensure .gitignore exists
    if [ ! -f ".gitignore" ]; then
        echo "Creating .gitignore file..."
        cat > .gitignore << EOL
.env
__pycache__/
*.pyc
.streamlit/
company_profiles.json
EOL
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo "❌ requirements.txt not found! Please create it first."
        exit 1
    fi
    
    # Stage files for commit
    git add .
    git add -f Procfile setup.sh app.json
    
    # Create commit
    read -p "Enter commit message (or press Enter for default): " commit_msg
    if [ -z "$commit_msg" ]; then
        commit_msg="Deploy Adcellerant Social Caption Generator"
    fi
    
    git commit -m "$commit_msg"
}

# Function to deploy to Streamlit Cloud
deploy_streamlit() {
    echo "☁️  Deploying to Streamlit Community Cloud..."
    echo ""
    echo "1. Push your code to GitHub:"
    echo "   git remote add origin https://github.com/USERNAME/REPOSITORY.git"
    echo "   git push -u origin main"
    echo ""
    echo "2. Visit: https://share.streamlit.io"
    echo "3. Connect your GitHub account"
    echo "4. Select your repository"
    echo "5. Add environment variables:"
    echo "   - OPENAI_API_KEY: [Your OpenAI API Key]"
    echo "   - APP_PASSWORD: Jax2021"
    echo ""
    echo "Your app will be available at:"
    echo "https://USERNAME-REPOSITORY-main.streamlit.app"
}

# Function to deploy to Heroku
deploy_heroku() {
    echo "🟣 Deploying to Heroku..."
    
    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        echo "❌ Heroku CLI not found. Please install it first:"
        echo "   https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    read -p "Enter your Heroku app name: " app_name
    read -p "Enter your OpenAI API key: " openai_key
    
    echo "Creating Heroku app..."
    heroku create $app_name
    
    echo "Setting environment variables..."
    heroku config:set OPENAI_API_KEY="$openai_key" --app $app_name
    heroku config:set APP_PASSWORD="Jax2021" --app $app_name
    
    echo "Deploying to Heroku..."
    git push heroku main
    
    echo "✅ Deployment complete!"
    echo "Your app is available at: https://$app_name.herokuapp.com"
}

# Function to show environment setup
show_env_setup() {
    echo "🔧 Environment Variables Setup"
    echo "============================="
    echo ""
    echo "Make sure to set these environment variables on your hosting platform:"
    echo ""
    echo "OPENAI_API_KEY = [Your OpenAI API Key]"
    echo "APP_PASSWORD = Jax2021"
    echo ""
    echo "⚠️  NEVER commit your .env file to GitHub!"
    echo "⚠️  Always use environment variables on hosting platforms!"
}

# Function to test local deployment
test_local() {
    echo "🧪 Testing local deployment..."
    
    if [ ! -f ".env" ]; then
        echo "❌ .env file not found! Creating template..."
        cat > .env << EOL
OPENAI_API_KEY=your_openai_key_here
APP_PASSWORD=Jax2021
EOL
        echo "📝 Please edit .env file with your actual OpenAI API key"
        exit 1
    fi
    
    echo "Starting local server..."
    streamlit run social_post_generator.py --server.port 8501
}

# Main menu
echo ""
echo "Choose deployment option:"
echo "1) 🧪 Test locally"
echo "2) ☁️  Deploy to Streamlit Community Cloud (FREE)"
echo "3) 🟣 Deploy to Heroku"
echo "4) 🔧 Show environment setup guide"
echo "5) 📦 Prepare files only (no deployment)"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        test_local
        ;;
    2)
        check_git
        prepare_deployment
        deploy_streamlit
        ;;
    3)
        check_git
        prepare_deployment
        deploy_heroku
        ;;
    4)
        show_env_setup
        ;;
    5)
        check_git
        prepare_deployment
        echo "✅ Files prepared for deployment!"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process complete!"
echo ""
echo "📚 For more deployment options, check PASSWORD_SETUP.md"
echo "🔐 Your app is password protected with: Jax2021"
echo "📞 Need help? Check the troubleshooting section in the documentation"
