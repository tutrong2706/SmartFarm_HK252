#!/usr/bin/env python3
"""
test_chatbot.py — Test script for AI Chatbot functionality
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    try:
        import langchain_google_genai
        print("  ✅ langchain_google_genai imported")
        
        import google.generativeai
        print("  ✅ google.generativeai imported")
        
        from chatbot import chat_with_ai, clear_history
        print("  ✅ chatbot module imported")
        
        from ai_config import GEMINI_API_KEY
        print("  ✅ ai_config imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_config():
    """Test if Gemini API key is configured"""
    print("\n🔍 Testing configuration...")
    from ai_config import GEMINI_API_KEY, LLM_MODEL
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("  ⚠️  GEMINI_API_KEY not configured properly")
        print("  📝 To configure:")
        print("     1. Get API key from https://aistudio.google.com")
        print("     2. Set GEMINI_API_KEY in backend/.env")
        return False
    
    print(f"  ✅ GEMINI_API_KEY is set (first 10 chars: {GEMINI_API_KEY[:10]}...)")
    print(f"  ✅ LLM_MODEL: {LLM_MODEL}")
    return True

def test_chat():
    """Test basic chat functionality"""
    print("\n🔍 Testing chat functionality...")
    from chatbot import chat_with_ai
    
    try:
        response = chat_with_ai(
            user_query="Xin chào! Bạn có thể giúp tôi về nông nghiệp không?",
            session_id="test_session"
        )
        
        if response and not response.startswith("❌"):
            print(f"  ✅ Chat response received (length: {len(response)} chars)")
            print(f"  📝 Sample response: {response[:100]}...")
            return True
        else:
            print(f"  ❌ Chat error: {response}")
            return False
            
    except Exception as e:
        print(f"  ❌ Chat test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 SmartFarm AI Chatbot Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Chat Functionality", test_chat),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} test error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Chatbot is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
