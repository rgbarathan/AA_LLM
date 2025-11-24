# 🔒 Quick Security Setup Guide

## First Time Setup (Choose One Method)

### Method 1: Automated Setup (Recommended)
```bash
./setup_secure.sh
```

### Method 2: Manual Setup
```bash
# 1. Copy the template
cp .env.example .env

# 2. Edit .env and add your API key
nano .env  # or use your preferred editor

# 3. Install dependencies
pip install -r requirements.txt
```

## Get Your API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

## Verify Setup

Run this to check if your API key is configured:
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ API Key configured!' if os.getenv('GEMINI_API_KEY') else '❌ API Key not found')"
```

## Common Issues

### Error: "GEMINI_API_KEY not found in environment variables"
**Solution**: Make sure you have created a `.env` file with your API key.

### Error: "ModuleNotFoundError: No module named 'dotenv'"
**Solution**: Install dependencies with `pip install -r requirements.txt`

### API key not working
**Solution**: 
1. Check for extra spaces in your `.env` file
2. Verify the key is valid at https://makersuite.google.com/app/apikey
3. Make sure `.env` is in the project root directory

## Security Checklist

- [ ] Created `.env` file from `.env.example`
- [ ] Added valid API key to `.env`
- [ ] Verified `.env` is in `.gitignore`
- [ ] Never committed `.env` to git
- [ ] Read `SECURITY.md` for best practices

## Need Help?

See `SECURITY.md` for detailed security guidelines and best practices.
