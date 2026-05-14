#!/usr/bin/env python3
"""
test_sql_agent.py — Test script for Text-to-SQL functionality
"""
import os
from dotenv import load_dotenv
from sql_agent import query_database, get_schema_info, test_sql_agent

def test_basic_queries():
    """Test basic SQL Agent queries"""
    print("\n" + "="*60)
    print("🧪 Testing Text-to-SQL Queries")
    print("="*60)
    
    test_queries = [
        "Có bao nhiêu khu vực trong hệ thống?",
        "Liệt kê tất cả các thiết bị",
        "Hiển thị các cảnh báo từ hôm qua",
        "Khu vực nào sử dụng cây cà chua?",
        "Có bao nhiêu thiết bị đang hoạt động?",
        "Danh sách các cảnh báo mới nhất",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}/{len(test_queries)}] ❓ {query}")
        print("-" * 60)
        
        result = query_database(query)
        
        if result["success"]:
            print(f"✅ Success")
            print(f"📝 Result: {result['result'][:200]}...")  # First 200 chars
        else:
            print(f"❌ Failed")
            print(f"❌ Error: {result['result']}")

def test_schema():
    """Test schema info retrieval"""
    print("\n" + "="*60)
    print("🗂️  Testing Database Schema Retrieval")
    print("="*60)
    
    schema_info = get_schema_info()
    print(schema_info[:500])  # Print first 500 chars
    print("\n... (truncated)")

def main():
    load_dotenv()
    
    print("\n" + "="*60)
    print("🤖 SmartFarm Text-to-SQL Test Suite")
    print("="*60)
    
    # Test 1: SQL Agent initialization
    print("\n[Test 1/3] SQL Agent Initialization")
    print("-" * 60)
    test_sql_agent()
    
    # Test 2: Schema retrieval
    print("\n[Test 2/3] Database Schema")
    print("-" * 60)
    test_schema()
    
    # Test 3: Basic queries
    test_basic_queries()
    
    print("\n" + "="*60)
    print("✅ Test suite completed!")
    print("="*60)

if __name__ == "__main__":
    main()
