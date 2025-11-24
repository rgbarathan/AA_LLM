# Security Guidelines

## API Key Management

This project uses the Google Gemini API, which requires an API key for authentication. **Never commit your API key to version control.**

### Setup Instructions

1. **Get Your API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create or select a project
   - Generate an API key

2. **Configure Environment Variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API key
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Verify Configuration**
   - The `.env` file is already in `.gitignore` and will not be committed
   - Never share your `.env` file or API key with others
   - Each team member should create their own `.env` file locally

### Best Practices

#### ✅ DO:
- Store API keys in environment variables using `.env` files
- Use `.env.example` as a template (without real keys)
- Keep `.env` in `.gitignore`
- Use different API keys for development and production
- Rotate API keys periodically
- Set up API usage quotas and monitoring in Google Cloud Console
- Revoke compromised keys immediately

#### ❌ DON'T:
- Hardcode API keys in source code
- Commit `.env` files to version control
- Share API keys via email, chat, or other insecure channels
- Use production API keys in development
- Include API keys in screenshots or documentation
- Log API keys in application logs

### Security Features Implemented

1. **Environment Variable Loading**: Using `python-dotenv` to load API keys from `.env` files
2. **Validation**: Code checks for API key presence and fails fast with helpful error messages
3. **Git Protection**: `.env` files are explicitly excluded in `.gitignore`
4. **Template Provided**: `.env.example` serves as a reference without exposing secrets

### If Your API Key is Compromised

1. **Immediately revoke the key** in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Generate a new API key
3. Update your `.env` file with the new key
4. If the key was committed to git:
   - Remove it from git history using `git filter-branch` or BFG Repo-Cleaner
   - Force push the cleaned history
   - Notify all team members to re-clone the repository

### Additional Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Python Dotenv Documentation](https://github.com/theskumar/python-dotenv)

### Reporting Security Issues

If you discover a security vulnerability in this project, please report it to the project maintainers privately before public disclosure.
