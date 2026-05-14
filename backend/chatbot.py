"""
chatbot.py — AI Agent Logic cho SmartFarm
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from ai_config import GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, CHATBOT_SYSTEM_PROMPT
from typing import Optional
import os
from sql_agent import query_database, get_schema_info
from rag_system import retrieve_documents, format_retrieved_docs, get_rag_system

# Khởi tạo Gemini LLM
def init_gemini_llm():
    """Khởi tạo Google Gemini LLM"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        google_api_key=GEMINI_API_KEY
    )
    return llm

# Lưu conversation history
conversation_history = {}

def _should_use_sql(query: str) -> bool:
    """Detect if question is asking for database queries"""
    sql_keywords = [
        "bao nhiêu", "có bao", "liệt kê", "danh sách", "hiển thị",
        "tất cả", "khu vực", "thiết bị", "cảnh báo", "cai đặt",
        "cây", "sensor", "temperature", "humidity", "status",
        "count", "show", "list", "display", "which", "where",
        "dữ liệu", "data", "thống kê", "stats", "quả lại", "hôm qua",
        "hôm nay", "tuần", "tháng", "năm", "cao nhất", "thấp nhất"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in sql_keywords)

def _should_use_rag(query: str) -> bool:
    """Detect if question would benefit from RAG (agricultural knowledge)"""
    rag_keywords = [
        "làm thế nào", "how to", "cách", "kỹ thuật", "technique",
        "bệnh", "disease", "sâu", "pest", "canh tác", "cultivation",
        "tối ưu", "optimal", "optimal", "best", "tốt nhất",
        "cà chua", "tomato", "dưa", "cucumber", "xà lách", "lettuce",
        "bón phân", "fertilize", "tưới", "irrigation", "ánh sáng", "light",
        "ngọn", "pruning", "tỉa", "bệnh phấn trắng", "powdery mildew",
        "thán thư", "early blight", "nấm", "fungus", "virus",
        "nhiệt độ tối ưu", "optimal temperature", "độ ẩm", "humidity",
        "thu hoạch", "harvest", "trồng", "planting", "gieo", "sowing"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in rag_keywords)

def chat_with_ai(user_query: str, session_id: str = "default", context: Optional[dict] = None) -> str:
    """
    Gửi câu hỏi đến AI và nhận phản hồi
    Tự động sử dụng SQL Agent hoặc RAG dựa trên nội dung câu hỏi
    
    Args:
        user_query: Câu hỏi từ người dùng
        session_id: ID của phiên chat (để lưu lịch sử)
        context: Thông tin ngữ cảnh (ví dụ: dữ liệu sensor hiện tại)
    
    Returns:
        Phản hồi từ AI
    """
    try:
        llm = init_gemini_llm()
        
        # Khởi tạo history nếu chưa có
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        system_prompt = CHATBOT_SYSTEM_PROMPT
        rag_context = ""
        
        # Kiểm tra nếu câu hỏi liên quan đến cơ sở dữ liệu (SQL)
        if _should_use_sql(user_query):
            sql_result = query_database(user_query)
            
            if sql_result["success"]:
                # Có kết quả từ DB, cho Gemini tóm tắt/giải thích
                rag_context = f"""
Dữ liệu từ cơ sở dữ liệu SmartFarm:
{sql_result['result']}

Vui lòng tóm tắt và giải thích những dữ liệu này bằng tiếng Việt, dưới dạng thân thiện với người nông dân.
"""
        
        # Kiểm tra nếu câu hỏi liên quan đến kiến thức nông nghiệp (RAG)
        elif _should_use_rag(user_query):
            # Lấy tài liệu liên quan từ RAG
            retrieved_docs = retrieve_documents(user_query, k=3)
            
            if retrieved_docs:
                rag_context = format_retrieved_docs(retrieved_docs)
                system_prompt += "\n\n📚 Bạn có quyền truy cập vào các tài liệu nông nghiệp. Sử dụng thông tin từ các tài liệu này để trả lời câu hỏi."
        
        # Xây dựng context message
        context_msg = ""
        if context:
            context_msg = f"\n\n📊 THÔNG TIN NGỮ CẢNH HỆ THỐNG:\n{context}"
        
        # Tạo messages để gửi tới LLM
        messages = [
            SystemMessage(content=system_prompt),
        ]
        
        # Thêm lịch sử hội thoại (giữ 5 messages gần nhất)
        for msg in conversation_history[session_id][-5:]:
            messages.append(msg)
        
        # Thêm câu hỏi mới với context
        full_query = rag_context + user_query + context_msg
        user_msg = HumanMessage(content=full_query)
        messages.append(user_msg)
        
        # Gọi LLM
        response = llm.invoke(messages)
        ai_response = response.content
        
        # Lưu vào history
        conversation_history[session_id].append(user_msg)
        conversation_history[session_id].append(response)
        
        return ai_response
    
    except Exception as e:
        return f"❌ Lỗi: {str(e)}\n💡 Hãy kiểm tra GEMINI_API_KEY trong .env file"

def clear_history(session_id: str = "default"):
    """Xóa lịch sử hội thoại của một phiên"""
    if session_id in conversation_history:
        del conversation_history[session_id]

def get_history(session_id: str = "default") -> list:
    """Lấy lịch sử hội thoại"""
    return conversation_history.get(session_id, [])
