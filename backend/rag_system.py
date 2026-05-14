"""
rag_system.py — Retrieval-Augmented Generation (RAG) System
Enables the chatbot to answer questions based on agricultural documents
"""
import os
from pathlib import Path
from typing import List, Optional, Dict
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain_core.documents import Document

load_dotenv()

# RAG Configuration
DOCS_PATH = "./data/agricultural_docs"
VECTOR_DB_PATH = "./data/vector_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "embedding-001"  # Google's embedding model

# Initialize vector store
_vector_store = None
_retriever = None

def init_rag_system():
    """Initialize RAG system with vector database"""
    global _vector_store, _retriever
    
    try:
        # Initialize embeddings using Google's model
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Load or create vector store
        if os.path.exists(VECTOR_DB_PATH) and len(os.listdir(VECTOR_DB_PATH)) > 0:
            # Load existing vector database
            _vector_store = Chroma(
                persist_directory=VECTOR_DB_PATH,
                embedding_function=embeddings,
                collection_name="agricultural_docs"
            )
            print(f"✅ Loaded existing vector DB with {_vector_store._collection.count()} documents")
        else:
            # Create new vector database from documents
            docs = load_documents()
            if docs:
                _vector_store = Chroma.from_documents(
                    documents=docs,
                    embedding=embeddings,
                    persist_directory=VECTOR_DB_PATH,
                    collection_name="agricultural_docs"
                )
                _vector_store.persist()
                print(f"✅ Created vector DB with {len(docs)} document chunks")
            else:
                print("⚠️  No documents found. RAG system will use defaults.")
                return None, None
        
        # Create retriever from vector store
        _retriever = _vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Retrieve top 3 most relevant documents
        )
        
        return _vector_store, _retriever
    
    except Exception as e:
        print(f"❌ RAG System initialization error: {e}")
        return None, None

def load_documents() -> List[Document]:
    """Load all documents from agricultural_docs folder"""
    try:
        docs_path = Path(DOCS_PATH)
        
        if not docs_path.exists():
            print(f"⚠️  Documents folder not found at {DOCS_PATH}")
            print("     Creating folder and using default documents...")
            docs_path.mkdir(parents=True, exist_ok=True)
            
            # Create some default documents
            create_default_documents()
        
        all_docs = []
        
        # Load PDF documents
        if list(docs_path.glob("*.pdf")):
            pdf_loader = DirectoryLoader(
                str(docs_path),
                glob="*.pdf",
                loader_cls=PyPDFLoader
            )
            all_docs.extend(pdf_loader.load())
            print(f"✅ Loaded PDFs")
        
        # Load TXT documents
        if list(docs_path.glob("*.txt")):
            txt_loader = DirectoryLoader(
                str(docs_path),
                glob="*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            all_docs.extend(txt_loader.load())
            print(f"✅ Loaded text files")
        
        # Split documents into chunks
        if all_docs:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = splitter.split_documents(all_docs)
            print(f"✅ Split into {len(chunks)} chunks")
            return chunks
        
        return []
    
    except Exception as e:
        print(f"❌ Document loading error: {e}")
        return []

def create_default_documents():
    """Create sample agricultural documents for demo"""
    docs_path = Path(DOCS_PATH)
    docs_path.mkdir(parents=True, exist_ok=True)
    
    # Sample document 1: Tomato cultivation
    tomato_doc = """
# Hướng dẫn canh tác cà chua

## Điều kiện khí hậu tối ưu
- Nhiệt độ: 20-28°C (tối ưu 24-26°C)
- Độ ẩm: 60-80%
- Ánh sáng: 12-16 giờ/ngày, cường độ 15,000-20,000 lux

## Các giai đoạn sinh trưởng
1. **Giai đoạn hạt nẫu**: 5-7 ngày
2. **Giai đoạn mầm**: 30-40 ngày
3. **Giai đoạn ra hoa**: 50-60 ngày
4. **Giai đoạn kết quả**: 60-90 ngày

## Quản lý sâu bệnh
- Bệnh phấn trắng: Sử dụng sulfur 80% hoặc neem oil
- Thán thư cà chua: Xoá lá nhiễm, tập trung tưới nước
- Sâu cuốn lá: Sử dụng Bt hoặc các thuốc sinh học

## Tưới nước
- Tần suất: Hàng ngày, tối ưu là tưới nhỏ giọt
- Lượng nước: 30-50mm/tuần tùy theo thời tiết
- Thời điểm tốt nhất: Sáng sớm hoặc chiều tối

## Thu hoạch
- Thời điểm: 60-90 ngày sau trồng
- Dấu hiệu chín: Quả chuyển từ xanh sang đỏ, mềm khi bấm nhẹ
- Năng suất: 30-50 tấn/ha/năm
"""
    
    # Sample document 2: Cucumber cultivation
    cucumber_doc = """
# Hướng dẫn canh tác dưa leo

## Đặc điểm sinh học
- Tuổi thọ: 45-65 ngày
- Nhiệt độ tối ưu: 18-25°C
- Không chịu được sương muối

## Chuẩn bị đất
- pH: 6.0-6.8
- Độ tơi xốp cao
- Giàu chất hữu cơ

## Bón phân
- Phân cơ bản: 10-15 tấn/ha
- Phân N-P-K: 300-400 kg/ha
- Chia nhiều lần: Lúc trồng, hoa, kết quả

## Điều chỉnh tập tính
- Buộc dây, cắt tỉa: Để tăng năng suất
- Giữ 1-2 nhánh chính
- Loại bỏ hoa đực không cần thiết

## Bệnh thường gặp
- Lùn dưa leo: Virus, truyền bởi rầy
- Bệnh thán thư: Tăng thông thoáng
- Bệnh phấn trắng: Xịt sulfur định kỳ

## Thu hoạch
- Thời điểm: 45-50 ngày sau trồng
- Tần suất: Hàng ngày để kích thích kết quả
- Tiêu chuẩn: Dài 20-25cm, còn tươi tốt
"""
    
    # Sample document 3: Lettuce cultivation
    lettuce_doc = """
# Hướng dẫn canh tác xà lách

## Điều kiện tối ưu
- Nhiệt độ: 15-20°C
- Độ ẩm: 70-80%
- Ánh sáng: 10-14 giờ/ngày

## Gieo trồng
- Thời gian: Quanh năm (tùy giống)
- Khoảng cách: 20-30cm giữa các cây
- Độ sâu: Nông, 0.5-1cm

## Chăm sóc
- Tưới: Đều đặn, tránh úng nước
- Cỏ dại: Tỏa loại sớm
- Bón phân: Ít hơn các loại khác

## Bệnh phổ biến
- Nấm tán: Tăng thông thoáng, xoá lá bệnh
- Bệnh héo: Liên quan đến tưới nước, chọn giống kháng bệnh
- Sâu bọ: Sử dụng mặt lưới, diệt côn trùng tự nhiên

## Thu hoạch
- Thời gian: 30-60 ngày tùy giống
- Phương pháp: Cắt lá từng chiếc hoặc cắt gốc
- Tươi độ: Thu hoạch sáng sớm, để nước
"""
    
    try:
        with open(docs_path / "tomato_cultivation.txt", "w", encoding="utf-8") as f:
            f.write(tomato_doc)
        print(f"✅ Created tomato_cultivation.txt")
        
        with open(docs_path / "cucumber_cultivation.txt", "w", encoding="utf-8") as f:
            f.write(cucumber_doc)
        print(f"✅ Created cucumber_cultivation.txt")
        
        with open(docs_path / "lettuce_cultivation.txt", "w", encoding="utf-8") as f:
            f.write(lettuce_doc)
        print(f"✅ Created lettuce_cultivation.txt")
    
    except Exception as e:
        print(f"❌ Error creating documents: {e}")

def retrieve_documents(query: str, k: int = 3) -> List[Dict]:
    """
    Retrieve relevant documents based on query
    
    Args:
        query: User question/search query
        k: Number of documents to retrieve
    
    Returns:
        List of retrieved documents with metadata
    """
    try:
        vector_store, retriever = get_rag_system()
        
        if not retriever:
            return []
        
        # Search for similar documents
        docs = retriever.invoke(query)
        
        result = []
        for doc in docs[:k]:
            result.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "relevance": "high"  # Could compute actual relevance score
            })
        
        return result
    
    except Exception as e:
        print(f"❌ Document retrieval error: {e}")
        return []

def get_rag_system():
    """Get or initialize RAG system"""
    global _vector_store, _retriever
    if _vector_store is None:
        _vector_store, _retriever = init_rag_system()
    return _vector_store, _retriever

def format_retrieved_docs(docs: List[Dict]) -> str:
    """Format retrieved documents for inclusion in prompt"""
    if not docs:
        return ""
    
    formatted = "\n\n📚 CÁC TÀI LIỆU LIÊN QUAN:\n"
    formatted += "=" * 60 + "\n"
    
    for i, doc in enumerate(docs, 1):
        formatted += f"\n[Tài liệu {i}] ({doc['source']})\n"
        formatted += "-" * 40 + "\n"
        # Truncate long content
        content = doc['content'][:300] + ("..." if len(doc['content']) > 300 else "")
        formatted += content + "\n"
    
    formatted += "\n" + "=" * 60 + "\n"
    return formatted

def test_rag():
    """Test RAG system with sample queries"""
    print("🧪 Testing RAG System...")
    
    test_queries = [
        "Nhiệt độ tối ưu cho cà chua là bao nhiêu?",
        "Làm thế nào để ngăn chặn bệnh phấn trắng?",
        "Bao lâu thì có thể thu hoạch dưa leo?",
        "Xà lách cần bao nhiêu ánh sáng mỗi ngày?",
    ]
    
    vector_store, retriever = get_rag_system()
    
    if not retriever:
        print("❌ RAG system not initialized")
        return
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        docs = retrieve_documents(query)
        print(f"📚 Found {len(docs)} relevant documents")
        for i, doc in enumerate(docs, 1):
            print(f"   [{i}] {doc['content'][:80]}...")

if __name__ == "__main__":
    test_rag()
