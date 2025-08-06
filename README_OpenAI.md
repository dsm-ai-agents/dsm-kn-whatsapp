# WhatsApp AI Chatbot - OpenAI Version

This version uses OpenAI's GPT models instead of Google Gemini.

## 🔄 Changes Made

### Dependencies
- Replaced `google-generativeai` with `openai`

### Environment Variables
Update your `.env` file:
```env
OPENAI_API_KEY="your_openai_api_key_here"
WASENDER_API_TOKEN="your_wasender_api_token_here"
```

### Model Configuration
- **Default Model**: `gpt-4o-mini` (cost-effective)
- **Alternative**: `gpt-4o` (higher quality, more expensive)
- **Max Tokens**: 1000
- **Temperature**: 0.7

## 💰 Cost Comparison

### OpenAI Pricing (as of 2024):
- **GPT-4o-mini**: $0.15/1M input tokens, $0.60/1M output tokens
- **GPT-4o**: $2.50/1M input tokens, $10.00/1M output tokens

### vs Gemini:
- **Gemini**: Free tier (1500 requests/month), then $0.35/1M tokens

## 🔧 Model Selection

To change the model, edit the `model` parameter in `get_openai_response()`:

```python
response = client.chat.completions.create(
    model="gpt-4o",  # Change this line
    messages=messages,
    max_tokens=1000,
    temperature=0.7
)
```

## 📊 Conversation History Format

OpenAI uses a different format than Gemini:

**OpenAI Format:**
```json
[
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"}
]
```

**Previous Gemini Format:**
```json
[
  {"role": "user", "parts": ["Hello"]},
  {"role": "model", "parts": ["Hi there!"]}
]
```

## 🚀 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file with OpenAI API key

3. Run the application:
```bash
python script.py
```

## 🔑 Getting OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up/Login
3. Navigate to API Keys section
4. Create a new API key
5. Copy and add to your `.env` file 