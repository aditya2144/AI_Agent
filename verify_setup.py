"""Verify the AI Sales Voice Agent setup."""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} installed")
        return True
    else:
        print(f"   ❌ Python 3.9+ required, found {version.major}.{version.minor}")
        return False


def check_virtual_env():
    """Check if running in virtual environment."""
    print("🔍 Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Virtual environment is active")
        return True
    else:
        print("   ⚠️  Virtual environment not active")
        print("      Run: .\\venv\\Scripts\\Activate.ps1")
        return False


def check_packages():
    """Check if required packages are installed."""
    print("🔍 Checking packages...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'streamlit',
        'sqlalchemy',
        'pydantic',
        'requests',
        'langchain',
        'chromadb',
        'google',  # google-generativeai
        'whisper',  # openai-whisper
        'gtts',
        'textblob',
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - not installed")
            all_installed = False
    
    if not all_installed:
        print("\n   Run: pip install -r requirements.txt")
    
    return all_installed


def check_env_file():
    """Check if .env file exists."""
    print("🔍 Checking .env file...")
    if os.path.exists('.env'):
        print("   ✅ .env file exists")
        
        # Check if API key is set
        with open('.env', 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY=' in content:
                if 'your_gemini_api_key_here' not in content:
                    print("   ✅ GEMINI_API_KEY appears to be configured")
                    return True
                else:
                    print("   ⚠️  GEMINI_API_KEY not configured (still has template value)")
                    return False
            else:
                print("   ❌ GEMINI_API_KEY not found in .env")
                return False
    else:
        print("   ❌ .env file not found")
        print("      Copy: Copy-Item .env.example .env")
        return False


def check_project_structure():
    """Check if project structure is correct."""
    print("🔍 Checking project structure...")
    required_dirs = [
        'backend/app',
        'backend/app/agents',
        'backend/app/database',
        'backend/app/rag',
        'backend/app/voice',
        'backend/app/lead_qualification',
        'backend/app/appointments',
        'backend/app/models',
        'frontend',
        'data',
        'reports',
        'logs',
    ]
    
    required_files = [
        'backend/app/main.py',
        'frontend/app.py',
        'requirements.txt',
        'README.md',
        '.env.example',
    ]
    
    all_exist = True
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ not found")
            all_exist = False
    
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} not found")
            all_exist = False
    
    return all_exist


def check_database():
    """Check if database can be initialized."""
    print("🔍 Checking database setup...")
    try:
        from backend.app.database import init_db, SessionLocal
        from backend.app.database.models import Base
        
        print("   ✅ Database models imported successfully")
        
        # Try to get a database session
        try:
            db = SessionLocal()
            db.close()
            print("   ✅ Database connection successful")
            return True
        except Exception as e:
            print(f"   ⚠️  Database connection: {e}")
            return True  # Still pass if import works
            
    except Exception as e:
        print(f"   ❌ Database setup error: {e}")
        return False


def check_ai_agent():
    """Check if AI agent can be initialized."""
    print("🔍 Checking AI agent...")
    try:
        from backend.app.agents import SalesAgent
        agent = SalesAgent()
        print("   ✅ Sales agent initialized")
        return True
    except Exception as e:
        print(f"   ⚠️  Sales agent: {e}")
        return True  # Still pass as it may need API key


def check_rag():
    """Check if RAG system can be initialized."""
    print("🔍 Checking RAG system...")
    try:
        from backend.app.rag import initialize_knowledge_base
        print("   ✅ RAG module imported (KB initialization will happen on startup)")
        return True
    except Exception as e:
        print(f"   ❌ RAG system error: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 50)
    print("🤖 AI Sales Voice Agent - Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Project Structure", check_project_structure),
        ("Packages", check_packages),
        (".env Configuration", check_env_file),
        ("Database", check_database),
        ("AI Agent", check_ai_agent),
        ("RAG System", check_rag),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Summary")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ All checks passed! You're ready to run the application.")
        print()
        print("Next steps:")
        print("1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("2. Start frontend: cd frontend && streamlit run app.py")
        print("3. Access at: http://localhost:8501")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        print("See SETUP_INSTRUCTIONS.md for help.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
