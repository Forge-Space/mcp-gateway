#!/bin/bash
# Python Environment Diagnostic Script
# Helps identify and resolve Python execution issues

echo "🔍 Python Environment Diagnostic Report"
echo "====================================="
echo ""

# System Information
echo "📋 System Information:"
echo "Operating System: $(uname -s)"
echo "Python Version: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "Python Path: $(which python3 2>/dev/null || echo 'Not found')"
echo "Pip Version: $(python3 -m pip --version 2>/dev/null || echo 'Not found')"
echo ""

# Check for virtual environment
echo "🐍 Virtual Environment Check:"
if [ -d ".venv" ]; then
    echo "✅ .venv directory exists"

    # Check if activated
    if [ "$VIRTUAL_ENV" != "" ]; then
        echo "✅ Virtual environment activated: $VIRTUAL_ENV"
        echo "Python in venv: $(which python)"
        echo "Pip in venv: $(which pip)"
    else
        echo "⚠️  Virtual environment not activated"
        echo "To activate: source .venv/bin/activate"
    fi

    # Check venv contents
    if [ -f ".venv/bin/python" ]; then
        echo "✅ Python executable exists in venv"
        echo "Venv Python version: $(.venv/bin/python --version 2>/dev/null || echo 'Error')"
    else
        echo "❌ Python executable missing in venv"
    fi
else
    echo "⚠️  No .venv directory found"
    echo "To create: python3 -m venv .venv"
fi
echo ""

# Test basic Python execution
echo "🧪 Basic Python Tests:"
echo "Testing python3 -c 'print(\"Hello World\")':"
python3 -c "print('Hello World')" 2>&1 || echo "❌ Failed with exit code $?"
echo ""

echo "Testing python3 --version:"
python3 --version 2>&1 || echo "❌ Failed with exit code $?"
echo ""

echo "Testing python3 -m pip --version:"
python3 -m pip --version 2>&1 || echo "❌ Failed with exit code $?"
echo ""

# Check for common issues
echo "🔍 Common Issues Check:"

# Check PATH
if echo "$PATH" | grep -q "/usr/bin/python3"; then
    echo "✅ System Python in PATH"
else
    echo "⚠️  System Python not in PATH"
fi

# Check for externally managed environment
echo "Checking for externally-managed-environment error:"
python3 -m pip install --dry-run numpy 2>&1 | grep -q "externally-managed-environment" && echo "⚠️  Externally managed environment detected" || echo "✅ No externally managed environment issue"
echo ""

# Check locale settings
echo "🌐 Locale Settings:"
echo "LANG: $LANG"
echo "LC_ALL: $LC_ALL"
echo "LC_CTYPE: $LC_CTYPE"
if [ "$LANG" != "en_US.UTF-8" ] && [ "$LC_ALL" != "en_US.UTF-8" ]; then
    echo "⚠️  Consider setting locale to en_US.UTF-8"
    echo "Add to ~/.zshrc: export LANG=en_US.UTF-8"
    echo "Add to ~/.zshrc: export LC_ALL=en_US.UTF-8"
else
    echo "✅ Locale settings appear correct"
fi
echo ""

# Check permissions
echo "🔒 Permissions Check:"
if [ -f ".venv/bin/python" ]; then
    if [ -x ".venv/bin/python" ]; then
        echo "✅ Python executable has execute permissions"
    else
        echo "❌ Python executable missing execute permissions"
        echo "Fix: chmod +x .venv/bin/python"
    fi
fi
echo ""

# Dependencies check
echo "📦 Dependencies Check:"
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt"
    if [ "$VIRTUAL_ENV" != "" ]; then
        echo "Checking installed packages..."
        python3 -m pip list 2>/dev/null | head -10 || echo "❌ Failed to list packages"
    else
        echo "⚠️  Activate virtual environment first"
    fi
else
    echo "No requirements.txt found"
fi
echo ""

# Recommendations
echo "💡 Recommendations:"
echo "=================="

if [ ! -d ".venv" ]; then
    echo "1. Create virtual environment:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
fi

if [ "$VIRTUAL_ENV" = "" ] && [ -d ".venv" ]; then
    echo "2. Activate virtual environment:"
    echo "   source .venv/bin/activate"
fi

echo "3. Install dependencies:"
echo "   python3 -m pip install -r requirements.txt"

echo "4. Test basic execution:"
echo "   python3 -c 'print(\"Test successful\")'"

echo ""
echo "🚀 Quick Fix Commands:"
echo "====================="
echo "# Create new venv (if needed)"
echo "python3 -m venv .venv"
echo ""
echo "# Activate venv"
echo "source .venv/bin/activate"
echo ""
echo "# Install dependencies"
echo "python3 -m pip install -r requirements.txt"
echo ""
echo "# Test execution"
echo "python3 -c 'print(\"Environment working!\")'"
echo ""
echo "# Run tests"
echo "python3 -m pytest tests/test_rag_manager.py -v"
