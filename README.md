# 🚀 Adcellerant Social Caption Generator v2.0

**Completely Refactored!** Enhanced AI-powered social media caption generator with modular architecture that creates engaging, brand-specific captions by analyzing your company's website and uploaded images.

## ✨ Features

### 🏗️ **NEW: Modular Architecture v2.0**
- **Complete Refactor**: 4,764-line monolithic file converted to clean modular structure
- **8 Specialized Modules**: Proper separation of concerns for better maintainability
- **Class-Based Design**: Object-oriented architecture with type hints and error handling
- **100% Backward Compatible**: All existing features preserved and enhanced

### 🚀 **Core Features**
- **� Advanced Image Processing**: Upload, edit (resize, crop, rotate, filters), batch processing
- **🌐 Intelligent Website Analysis**: Multi-page scraping for comprehensive brand understanding
- **🤖 Dual AI Models**: GPT-4o (premium) and GPT-4o-mini (cost-effective) options
- **📱 Platform Templates**: Pre-built templates for Instagram, Facebook, LinkedIn, Twitter, TikTok
- **� Company Profiles**: Save and reuse business information for consistency
- **� Usage Analytics**: Track caption generation, usage patterns, and performance metrics
- **� Feedback System**: Built-in bug reporting and feature request system
- **🎨 Professional UI**: Enhanced styling, responsive design, and intuitive workflow

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

### Method 1: New Modular Application (Recommended)
```bash
streamlit run main.py
```

### Method 2: Using Batch File (Windows)
```bash
run_social_generator.bat
```

### Method 3: Original Application (Legacy)
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

## 📁 Project Structure (v2.0 - Modular Architecture)

```
Social Post Generator/
├── 🚀 main.py                    # New modular entry point (517 lines)
├── 📜 social_post_generator.py   # Original monolithic file (4,764 lines - legacy)
├── 📁 config/                   # Application configuration
│   ├── constants.py             # App constants and settings (52 lines)
│   └── settings.py              # Data classes and configuration objects (28 lines)
├── 📁 modules/                  # Core business logic modules
│   ├── auth.py                  # Authentication and session management (94 lines)
│   ├── captions.py              # Caption tracking and analytics (312 lines)
│   ├── companies.py             # Company profile management (298 lines)
│   ├── website_analysis.py      # Website analysis engine (273 lines)
│   ├── image_processing.py      # Image editing and batch processing (571 lines)
│   └── templates.py             # Social media templates and analytics (557 lines)
├── 📁 utils/                    # Shared utilities
│   ├── file_ops.py              # JSON file operations (71 lines)
│   └── helpers.py               # Common utility functions (119 lines)
├── 📁 .venv/                    # Virtual environment
├── 🔐 .env                      # API keys (create this)
├── requirements.txt             # Dependencies
├── run_social_generator.bat     # Windows launcher
└── README.md                    # This documentation

🎯 Total Refactored Code: ~2,900 lines across 10 files
📊 Code Reduction: ~40% while adding new features
✅ Maintainability: Significantly improved
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
