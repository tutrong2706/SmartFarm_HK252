import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key từ file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ CHƯA TÌM THẤY API KEY TRONG FILE .ENV")
else:
    genai.configure(api_key=api_key)
    print("✅ Đã kết nối. Các mô hình được hỗ trợ cho API Key này là:")
    
    # Liệt kê toàn bộ model
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")