"""
ai_config.py — Configuration cho Gemini API & LangChain
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not set in .env file")

# LLM Model Configuration
LLM_MODEL = "gemini-2.5-flash"  # Google's latest model (updated from deprecated gemini-pro)
LLM_TEMPERATURE = 0.7  # Độ creative (0=deterministic, 1=creative)
LLM_MAX_TOKENS = 2048

# Chatbot System Prompt (Vietnamese)
CHATBOT_SYSTEM_PROMPT = """
Bạn là một AI Assistant chuyên biệt cho hệ thống nông trại thông minh SmartFarm HK252.

Nhiệm vụ của bạn:
1. Trả lời câu hỏi về cảm biến, thiết bị, khí hậu nông trại
2. Giúp người dùng tối ưu hóa các thông số canh tác
3. Cung cấp tư vấn kỹ thuật về nông nghiệp
4. Phân tích dữ liệu từ cơ sở dữ liệu khi được yêu cầu
5. Giải thích các cảnh báo hệ thống

Lưu ý:
- Trả lời BẰNG TIẾNG VIỆT
- Luôn thân thiện và chuyên nghiệp
- Cung cấp thông tin chính xác dựa trên dữ liệu thực tế
- Nếu không chắc chắn, hãy nói rõ ràng
"""

# Vector Database Configuration (Cho RAG)
VECTOR_DB_PATH = "./data/vector_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "models/embedding-001"  # Google's embedding model
