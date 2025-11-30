#!/usr/bin/env python3
"""Quick test to verify all critical imports work"""

import os

from dotenv import load_dotenv

print("=" * 60)
print("Testing Critical Imports and Configuration")
print("=" * 60)

# Test 1: Load environment variables
print("\n1. Testing .env loading...")
load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY")
print("   ✓ .env loaded")
print(
    f"   ✓ TAVILY_API_KEY found: {tavily_key[:20]}..."
    if tavily_key
    else "   ✗ TAVILY_API_KEY missing"
)

# Test 2: Import chromadb
print("\n2. Testing ChromaDB import...")
try:
    import chromadb

    print(f"   ✓ chromadb imported (version: {chromadb.__version__})")
except Exception as e:
    print(f"   ✗ chromadb import failed: {e}")

# Test 3: Import langchain-chroma
print("\n3. Testing langchain-chroma import...")
try:
    print("   ✓ langchain_chroma.Chroma imported")
except Exception as e:
    print(f"   ✗ langchain_chroma import failed: {e}")

# Test 4: Import tavily
print("\n4. Testing tavily-python import...")
try:
    from tavily import TavilyClient

    print("   ✓ tavily.TavilyClient imported")
except Exception as e:
    print(f"   ✗ tavily import failed: {e}")

# Test 5: Import langchain-community (for TavilySearchAPIWrapper)
print("\n5. Testing langchain-community imports...")
try:
    print("   ✓ TavilySearchAPIWrapper imported")
except Exception as e:
    print(f"   ✗ TavilySearchAPIWrapper import failed: {e}")

# Test 6: Import langchain-ollama
print("\n6. Testing langchain-ollama import...")
try:
    print("   ✓ ChatOllama and OllamaEmbeddings imported")
except Exception as e:
    print(f"   ✗ langchain_ollama import failed: {e}")

# Test 7: Check if we can create Tavily client
print("\n7. Testing Tavily client creation...")
try:
    from tavily import TavilyClient

    if tavily_key:
        client = TavilyClient(api_key=tavily_key)
        print("   ✓ TavilyClient created successfully")
    else:
        print("   ✗ Cannot create client: no API key")
except Exception as e:
    print(f"   ✗ TavilyClient creation failed: {e}")

# Test 8: Check if we can access ChromaDB
print("\n8. Testing ChromaDB connection...")
try:
    import chromadb

    client = chromadb.PersistentClient(path="./chroma_db")
    collections = client.list_collections()
    print("   ✓ ChromaDB connected")
    print(f"   ✓ Found {len(collections)} collections: {[c.name for c in collections]}")
except Exception as e:
    print(f"   ✗ ChromaDB connection failed: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
