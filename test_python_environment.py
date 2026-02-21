#!/usr/bin/env python3
"""
Simple Python Environment Test
Tests basic Python functionality without external dependencies
"""

import sys
import os

def test_basic_functionality():
    """Test basic Python functionality"""
    print("🧪 Python Environment Test")
    print("=" * 30)
    
    # Test Python version
    print(f"✅ Python Version: {sys.version}")
    print(f"✅ Python Executable: {sys.executable}")
    print(f"✅ Platform: {sys.platform}")
    
    # Test basic operations
    try:
        result = 2 + 2
        assert result == 4
        print("✅ Basic arithmetic: PASS")
    except Exception as e:
        print(f"❌ Basic arithmetic: FAIL - {e}")
    
    # Test string operations
    try:
        test_str = "Hello, World!"
        assert test_str == "Hello, World!"
        print("✅ String operations: PASS")
    except Exception as e:
        print(f"❌ String operations: FAIL - {e}")
    
    # Test imports
    try:
        import json
        import datetime
        print("✅ Standard library imports: PASS")
    except Exception as e:
        print(f"❌ Standard library imports: FAIL - {e}")
    
    # Test file operations
    try:
        with open("/tmp/test_python_env.txt", "w") as f:
            f.write("test")
        with open("/tmp/test_python_env.txt", "r") as f:
            content = f.read()
        os.remove("/tmp/test_python_env.txt")
        assert content == "test"
        print("✅ File operations: PASS")
    except Exception as e:
        print(f"❌ File operations: FAIL - {e}")
    
    # Test virtual environment
    if hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'):
        print("✅ Virtual environment: ACTIVE")
        print(f"   Base prefix: {getattr(sys, 'base_prefix', getattr(sys, 'real_prefix', 'N/A'))}")
        print(f"   Current prefix: {sys.prefix}")
    else:
        print("⚠️  Virtual environment: NOT ACTIVE (using system Python)")
    
    # Test environment variables
    print(f"✅ PATH: {os.environ.get('PATH', 'Not set')[:50]}...")
    print(f"✅ PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    print("\n🎯 Test Summary:")
    print("If all tests pass, Python environment is working correctly.")
    print("If tests fail, check virtual environment setup and permissions.")

def test_rag_imports():
    """Test RAG-related imports"""
    print("\n🔍 RAG Import Test")
    print("=" * 20)
    
    try:
        # Test if we can import from our project structure
        sys.path.insert(0, '/Users/lucassantana/Desenvolvimento/mcp-gateway')
        
        # Test basic imports (without executing)
        import ast
        with open('/Users/lucassantana/Desenvolvimento/mcp-gateway/tool_router/mcp_tools/rag_manager.py', 'r') as f:
            code = f.read()
        
        # Parse the AST to check syntax
        tree = ast.parse(code)
        print("✅ RAG Manager syntax: VALID")
        
        # Check for key components
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.Class)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        print(f"✅ Classes found: {len(classes)} ({', '.join(classes[:3])})")
        print(f"✅ Functions found: {len(functions)}")
        
        # Check for specific components
        if 'RAGManagerTool' in classes:
            print("✅ RAGManagerTool class: FOUND")
        else:
            print("❌ RAGManagerTool class: NOT FOUND")
            
        if 'rag_manager_handler' in functions:
            print("✅ rag_manager_handler function: FOUND")
        else:
            print("❌ rag_manager_handler function: NOT FOUND")
            
    except Exception as e:
        print(f"❌ RAG import test failed: {e}")
        print("This might be due to missing files or path issues")

if __name__ == "__main__":
    test_basic_functionality()
    test_rag_imports()
    print("\n🚀 Environment test completed!")