"""
Simple test script to verify OpenAI API is working
Just making a basic call to see if the key is valid
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from openai import OpenAI


def test_openai():
    """Test OpenAI API connection"""
    print("Testing OpenAI API connection...")
    print(f"API Key present: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        print("ERROR: OpenAI API key not set in .env file")
        print("Please set OPENAI_API_KEY in your .env file")
        return False
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Make a simple test call
        model = settings.OPENAI_MODEL
        print(f"Using model: {model}")
        print("Making test API call...")
        # gpt-5.2 uses max_completion_tokens instead of max_tokens
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, OpenAI API is working!' if you can read this."}
            ],
            max_completion_tokens=50
        )
        
        message = response.choices[0].message.content
        print(f"Response: {message}")
        print("✅ OpenAI API test successful!")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI API Test")
    print("=" * 60)
    print()
    
    success = test_openai()
    
    print()
    print("=" * 60)
    sys.exit(0 if success else 1)

