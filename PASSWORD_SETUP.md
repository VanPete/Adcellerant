# 🔐 Password Protection Setup Guide

## Overview
Your Adcellerant Social Caption Generator now has password protection to control access while still allowing authorized users to utilize the application.

## 🚀 Quick Setup (Simple Password)

### Current Setup
The app is already configured with simple password protection:

- **Default Password:** `adcellerant2025`
- **Location:** Set in `.env` file as `APP_PASSWORD`

### How to Change Password

1. **Edit the `.env` file:**
   ```
   APP_PASSWORD=your_new_password_here
   ```

2. **Restart the Streamlit application**

### How Users Access the App

1. Navigate to your Streamlit app URL
2. Enter the password when prompted
3. Click enter or the login button
4. Access granted for the session

## 🔒 Enhanced Security Options

For more advanced features, you can switch to the enhanced authentication system:

### Features of Enhanced Auth:
- ✅ Multiple user support
- ✅ Different access levels (Demo, Standard, Admin)
- ✅ Session management with expiration
- ✅ Login attempt tracking
- ✅ Better security with password hashing

### To Enable Enhanced Auth:

1. **Replace the authentication section in `social_post_generator.py`:**

```python
# Replace the current auth import
from enhanced_auth import enhanced_password_check, show_session_info, demo_mode_warning

# In main() function, replace:
if not check_password():
    return

# With:
if not enhanced_password_check():
    return
```

2. **Configure passwords in `auth_config.py`:**

```python
SIMPLE_PASSWORDS = {
    "your_main_password": {"level": "standard"},
    "admin_password_here": {"level": "admin"},
    "demo123": {"level": "demo"}  # Limited features
}
```

## 📱 Access Levels Explained

### Demo Level
- Basic caption generation
- Limited to 5 captions per session
- No company profile saving
- Basic website analysis

### Standard Level  
- Full caption generation
- Unlimited usage
- Company profile management
- Full website analysis
- Batch processing

### Admin Level
- All Standard features
- Access to usage analytics
- User management (if implemented)
- System configuration options

## 🌐 Deployment Options for Public Domain

### Option 1: Streamlit Community Cloud (FREE & EASIEST)
**Best for:** Quick deployment, free hosting, automatic updates

#### Steps:
1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit with password protection"
   git branch -M main
   git remote add origin https://github.com/yourusername/adcellerant-caption-generator.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Choose `social_post_generator.py` as main file
   - Add environment variables (OPENAI_API_KEY, APP_PASSWORD)

3. **Your app will be available at:**
   `https://yourusername-adcellerant-caption-generator-main.streamlit.app`

4. **Custom domain (optional):**
   - Upgrade to Streamlit Teams ($20/month)
   - Add your custom domain in settings

### Option 2: Heroku (SIMPLE & RELIABLE)
**Best for:** Custom domains, professional deployment, scaling

#### Steps:
1. **Create Heroku files:**
   ```bash
   # Create requirements.txt if not exists
   pip freeze > requirements.txt
   ```

2. **Add Heroku-specific files:**
   - `Procfile` ✅ (created)
   - `setup.sh` ✅ (created) 
   - `app.json` ✅ (created)

3. **Deploy to Heroku:**
   ```bash
   # Install Heroku CLI, then:
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY="your_openai_key_here"
   heroku config:set APP_PASSWORD="Jax2021"
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

4. **Your app will be available at:**
   `https://your-app-name.herokuapp.com`

5. **Add custom domain:**
   ```bash
   heroku domains:add yourdomain.com
   heroku certs:auto:enable
   ```

### Option 3: DigitalOcean App Platform (RECOMMENDED)
**Best for:** Professional deployment, custom domains, good performance

#### Steps:
1. **Push code to GitHub** (same as Option 1)

2. **Deploy on DigitalOcean:**
   - Visit [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
   - Connect GitHub repository
   - Configure build settings:
     - Build Command: `pip install -r requirements.txt`
     - Run Command: `streamlit run social_post_generator.py --server.port=$PORT --server.address=0.0.0.0`

3. **Set environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI key
   - `APP_PASSWORD`: Jax2021

4. **Custom domain setup:**
   - Add domain in DigitalOcean dashboard
   - Update DNS records at your domain provider
   - SSL automatically provided

### Option 4: Railway (SIMPLE & FAST)
**Best for:** Quick deployment with custom domains

#### Steps:
1. **Visit [railway.app](https://railway.app)**
2. **Connect GitHub repository**
3. **Set environment variables:**
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
4. **Custom domain:** Available in settings

### Option 5: Render (FREE TIER AVAILABLE)
**Best for:** Free hosting with custom domains

#### Steps:
1. **Visit [render.com](https://render.com)**
2. **Create new Web Service**
3. **Connect GitHub repository**
4. **Settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run social_post_generator.py --server.port=$PORT --server.address=0.0.0.0`

## 🔗 Custom Domain Setup (General Steps)

### 1. Purchase Domain
- **Recommended providers:** Namecheap, Google Domains, Cloudflare
- **Cost:** $10-15/year for .com domains

### 2. Configure DNS
```
Type: CNAME
Name: www (or @)
Value: your-app-url-from-hosting-provider
TTL: 300
```

### 3. SSL Certificate
- Most platforms provide free SSL automatically
- Your site will be accessible via `https://yourdomain.com`

## 🚀 Quick Start Deployment (Recommended Path)

### For Beginners: Streamlit Community Cloud
1. **Upload to GitHub**
2. **Deploy on Streamlit Cloud** 
3. **Share the URL** (format: `https://username-repo-main.streamlit.app`)

### For Custom Domain: DigitalOcean
1. **GitHub → DigitalOcean App Platform**
2. **Add custom domain** in dashboard
3. **Professional URL** like `https://captions.yourdomain.com`

## 💰 Cost Comparison

| Platform | Free Tier | Custom Domain | Monthly Cost |
|----------|-----------|---------------|--------------|
| Streamlit Cloud | ✅ Yes | ❌ No (Teams only) | $0 - $20 |
| Heroku | ❌ No | ✅ Yes | $7 - $25 |
| DigitalOcean | ❌ No | ✅ Yes | $5 - $12 |
| Railway | ✅ Limited | ✅ Yes | $0 - $5 |
| Render | ✅ Yes | ✅ Yes | $0 - $7 |

## 🔐 Security for Public Deployment

### Environment Variables Setup
```bash
# Never commit these to GitHub!
OPENAI_API_KEY=your_actual_key_here
APP_PASSWORD=Jax2021
```

### .gitignore File (Important!)
```
.env
__pycache__/
*.pyc
.streamlit/
company_profiles.json
```

### Additional Security
1. **Rate limiting** (implement if high traffic)
2. **HTTPS only** (provided by most platforms)
3. **Regular password changes**
4. **Monitor usage** through OpenAI dashboard
```dockerfile
# Example Dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "social_post_generator.py"]
```

## 🔧 Password Management

### Sharing Access
1. **For teams:** Use the same password in `.env`
2. **For clients:** Create separate passwords with appropriate access levels
3. **For demos:** Use demo-level passwords

### Security Best Practices
1. **Use strong passwords** (mix of letters, numbers, symbols)
2. **Change passwords regularly** (monthly/quarterly)
3. **Don't share passwords** in plain text emails
4. **Use environment variables** for sensitive data
5. **Monitor access logs** if using enhanced auth

### Example Strong Passwords:
- `Adcellerant@2025!`
- `SocialAI#Caption$`
- `Marketing&Tools2025`

## 🛠️ Troubleshooting

### Common Issues:

**"Password not working"**
- Check `.env` file exists and has correct password
- Restart Streamlit application
- Verify no extra spaces in password

**"Authentication failed multiple times"**
- Wait a few minutes and try again
- Clear browser cache/cookies
- Contact administrator

**"Session expired"**
- Normal behavior after 24 hours
- Simply re-enter password

### Reset Password:
1. Edit `.env` file
2. Restart application
3. Inform users of new password

## 📞 Support

For technical support with password protection:
1. Check this README first
2. Verify `.env` configuration
3. Test with default password
4. Contact your development team

## 🔄 Updates

When updating the application:
1. Passwords remain in `.env` file
2. Enhanced auth settings in `auth_config.py`
3. No user data is lost during updates
4. Sessions may need re-authentication after updates

---
*Last updated: January 2025*
