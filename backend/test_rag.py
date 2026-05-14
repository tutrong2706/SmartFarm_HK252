#!/usr/bin/env python3
"""
test_rag.py — Test script for RAG (Retrieval-Augmented Generation) System
"""
import os
from dotenv import load_dotenv
from rag_system import test_rag, retrieve_documents, get_rag_system

def test_rag_retrieval():
    """Test document retrieval"""
    print("\n" + "="*60)
    print("🧪 Testing RAG Document Retrieval")
    print("="*60)
    
    test_queries = [
        "Nhiệt độ tối ưu cho cà chua là bao nhiêu?",
        "Làm thế nào để ngăn chặn bệnh phấn trắng?",
        "Bao lâu thì có thể thu hoạch dưa leo?",
        "Xà lách cần bao nhiêu ánh sáng mỗi ngày?",
        "Kỹ thuật tưới nước cho cây cà chua",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}/{len(test_queries)}] ❓ {query}")
        print("-" * 60)
        
        docs = retrieve_documents(query, k=3)
        
        if docs:
            print(f"✅ Found {len(docs)} relevant documents")
            for j, doc in enumerate(docs, 1):
                source = doc['source'].split('/')[-1]
                print(f"\n   [{j}] Source: {source}")
                print(f"       {doc['content'][:150]}...")
        else:
            print("⚠️  No documents found")

def test_rag_integration():
    """Test RAG system integration"""
    print("\n" + "="*60)
    print("🔗 Testing RAG System Integration")
    print("="*60)
    
    from chatbot import chat_with_ai
    
    test_questions = [
        "Cà chua cần bao nhiêu độ ẩm?",
        "Kỹ thuật canh tác xà lách tốt nhất là gì?",
        "Bệnh nấm tán trên dưa leo được xử lý như thế nào?",
    ]
    
    print("\n⚠️  Note: This test requires GEMINI_API_KEY to be configured")
    print("   Skipping actual LLM calls for now...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"[Test {i}/{len(test_questions)}] ❓ {question}")
        
        # Retrieve documents
        docs = retrieve_documents(question)
        print(f"   📚 {len(docs)} documents retrieved")
        
        # In real scenario, would call chat_with_ai
        # which would use these docs as context
        print(f"   ✅ Would pass docs to Gemini for contextualized answer\n")

def test_vector_store():
    """Test vector store status"""
    print("\n" + "="*60)
    print("📊 Testing Vector Store Status")
    print("="*60)
    
    vector_store, retriever = get_rag_system()
    
    if vector_store is None:
        print("⚠️  Vector store not initialized")
        return
    
    print("✅ Vector store initialized")
    print(f"   Type: {type(vector_store).__name__}")
    
    if hasattr(vector_store, '_collection'):
        doc_count = vector_store._collection.count()
        print(f"   Documents: {doc_count}")
    
    if hasattr(vector_store, 'persist_directory'):
        print(f"   Persist dir: {vector_store.persist_directory}")

def main():
    load_dotenv()
    
    print("\n" + "="*60)
    print("🤖 SmartFarm RAG System Test Suite")
    print("="*60)
    
    # Test 1: Initialize RAG
    print("\n[Test 1/4] RAG System Initialization")
    print("-" * 60)
    test_rag()
    
    # Test 2: Vector store status
    print("\n[Test 2/4] Vector Store Status")
    test_vector_store()
    
    # Test 3: Document retrieval
    test_rag_retrieval()
    
    # Test 4: Integration
    test_rag_integration()
    
    print("\n" + "="*60)
    print("✅ RAG test suite completed!")
    print("="*60)

if __name__ == "__main__":
    main()
