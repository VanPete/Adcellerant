# 🚀 Adcellerant Social Caption Generator

Enhanced AI-powered social media caption generator that creates engaging, brand-specific captions by analyzing your company's website and uploaded images.

## ✨ Features

- **📸 Multiple Image Sources**: Upload files, paste from clipboard, or use website images
- **🌐 Website Scraping**: Automatically analyzes company websites for brand alignment
- **🖼️ Website Image Extraction**: Finds and suggests images from company websites
- **🤖 AI-Powered**: Uses OpenAI's GPT-4o/GPT-4o-mini with vision capabilities
- **📱 Platform Optimized**: Captions ready for Instagram, Facebook, LinkedIn
- **🎨 Style Customization**: Choose from Professional, Casual, Inspirational, Educational, or Promotional tones
- **📏 Length Control**: Short, Medium, or Long caption options
- **🎯 Call-to-Action Options**: Toggle subtle CTAs on/off
- **💰 Cost Control**: Choose between premium (GPT-4o) or cost-effective (GPT-4o-mini) models
- **📋 Advanced UI**: Individual caption copying, clipboard support, professional interface
- **⚡ Smart Caching**: Faster repeated website analysis
- **🚫 Clean Output**: No emojis or hashtags - professional storytelling focus

## 🛠️ Setup

### Prerequisites
- Python 3.13+
- OpenAI API key

### Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Create `.env` file** with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 🚀 Usage

### Method 1: Using Batch File (Windows)
```bash
run_social_generator.bat
```

### Method 2: Command Line
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run the application
streamlit run social_post_generator.py
```

### Method 3: Direct Streamlit
```bash
streamlit run social_post_generator.py
```

## 📋 How It Works

1. **📸 Upload Image**: Choose your social media photo
2. **🏢 Enter Business Info**: Type your business name or category
3. **🌐 Add Website (Optional)**: Provide company URL for brand-specific content
4. **⚡ Generate**: Get 3 professional, ready-to-post captions!

## 🎯 Example Usage

- **Restaurant**: Upload food photo + "Italian Restaurant" + olivegarden.com
- **Fitness**: Upload workout photo + "Fitness Studio" + orangetheory.com  
- **Tech**: Upload office photo + "Software Company" + microsoft.com

## 💡 Features & Benefits

| Feature | Benefit |
|---------|---------|
| Website Analysis | Brand-aligned, authentic captions |
| Dual AI Models | Balance quality vs cost |
| Smart Caching | Faster repeated website analysis |
| Download Captions | Easy copy-paste to social platforms |
| Error Handling | Graceful failure with helpful messages |

## 📁 Project Structure

```
Adcellerant/
├── .env                    # API keys (create this)
├── .venv/                  # Virtual environment
├── requirements.txt        # Dependencies
├── social_post_generator.py # Main Streamlit app
├── run_social_generator.bat # Windows launcher
└── README.md              # This file
```

## 🔧 Dependencies

- **streamlit**: Web UI framework
- **openai**: GPT-4 vision API
- **beautifulsoup4**: Website scraping
- **requests**: HTTP requests
- **Pillow**: Image processing
- **python-dotenv**: Environment variables

## 🛡️ Error Handling

The app handles:
- Missing API keys
- Invalid websites
- Network timeouts
- API quota limits
- Unsupported image formats

## 💰 Cost Management

- **GPT-4o-mini**: ~60% cheaper, great for testing
- **GPT-4o**: Premium quality for production use
- **Smart Caching**: Reduces repeated API calls

## 🎨 Customization

The Streamlit app is easily customizable:
- UI layout and styling
- Prompt engineering
- Website analysis rules
- Caption formatting

---

**Built with ❤️ for Adcellerant**
