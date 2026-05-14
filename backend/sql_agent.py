"""
sql_agent.py — Text-to-SQL Agent using LangChain
Allows natural language questions to be converted to SQL queries against the SmartFarm database
"""
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import inspect
from database import engine
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize database connection for SQL Agent
def init_sql_agent():
    """Initialize LangChain SQL Agent connected to SmartFarm database"""
    try:
        # Create SQLAlchemy engine for LangChain
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:27062005@localhost:5432/smart_farm_db"
        )
        
        # Initialize SQL Database for LangChain
        db = SQLDatabase.from_uri(
            db_url,
            schema="public",
            include_tables=[
                "user",
                "zone",
                "device",
                "device_type",
                "crop_setting",
                "alert_log"
            ]
        )
        
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.0,  # Use 0 for SQL generation (deterministic)
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Create SQL Agent (using default agent type)
        agent = create_sql_agent(
            llm,
            db=db,
            verbose=False,
            return_intermediate_steps=False,
            max_iterations=5
        )
        
        return agent, db
    
    except Exception as e:
        print(f"❌ SQL Agent initialization error: {e}")
        return None, None

# Global agent instance
_sql_agent = None
_sql_db = None

def get_sql_agent():
    """Get or create SQL Agent instance"""
    global _sql_agent, _sql_db
    if _sql_agent is None:
        _sql_agent, _sql_db = init_sql_agent()
    return _sql_agent, _sql_db

def query_database(question: str) -> dict:
    """
    Execute a SQL query based on natural language question
    
    Args:
        question: Natural language query in Vietnamese or English
        e.g., "Có bao nhiêu thiết bị đang hoạt động?" 
              "Hiển thị tất cả cảnh báo ngôi nhà hôm qua"
              "Khu vực nào sử dụng cây cà chua?"
    
    Returns:
        {
            "success": bool,
            "result": query results or error message,
            "sql_query": the generated SQL (for transparency),
            "row_count": number of rows returned
        }
    """
    try:
        agent, db = get_sql_agent()
        
        if not agent or not db:
            return {
                "success": False,
                "result": "SQL Agent không khả dụng. Kiểm tra cấu hình cơ sở dữ liệu.",
                "sql_query": None,
                "row_count": 0
            }
        
        # Execute agent with the question
        response = agent.invoke({"input": question})
        
        result_text = response.get("output", "Không có kết quả")
        
        return {
            "success": True,
            "result": result_text,
            "sql_query": None,  # Agent doesn't expose raw SQL easily
            "row_count": None  # Depends on result format
        }
    
    except Exception as e:
        return {
            "success": False,
            "result": f"Lỗi truy vấn: {str(e)}",
            "sql_query": None,
            "row_count": 0
        }

def get_schema_info() -> str:
    """Get readable database schema information for context"""
    try:
        inspector = inspect(engine)
        
        schema_info = "📊 SmartFarm Database Schema:\n\n"
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            schema_info += f"**{table_name}**:\n"
            for col in columns:
                col_type = str(col['type'])
                nullable = "optional" if col['nullable'] else "required"
                schema_info += f"  - {col['name']}: {col_type} ({nullable})\n"
            schema_info += "\n"
        
        return schema_info
    
    except Exception as e:
        return f"Could not retrieve schema: {e}"

def test_sql_agent():
    """Test the SQL Agent with sample queries"""
    print("🧪 Testing SQL Agent...")
    
    test_questions = [
        "Có bao nhiêu khu vực trong hệ thống?",
        "Liệt kê tất cả các thiết bị",
        "Có bao nhiêu cảnh báo hôm nay?",
        "Khu vực nào có máy bơm?",
    ]
    
    agent, db = get_sql_agent()
    
    if not agent:
        print("❌ SQL Agent initialization failed")
        return
    
    print("✅ SQL Agent initialized")
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        result = query_database(question)
        print(f"📝 Result: {result['result']}")

if __name__ == "__main__":
    test_sql_agent()
