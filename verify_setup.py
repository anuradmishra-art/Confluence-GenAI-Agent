"""
Setup Verification Script
Run this to check if your environment is configured correctly
"""

import os
import sys
from dotenv import load_dotenv

def check_python_version():
    """Check if Python version is 3.9+ (required for atlassian library)"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is too old. Need 3.9+")
        print("   The atlassian-python-api library requires Python 3.9 or higher")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        ('atlassian', 'atlassian'),
        ('openai', 'openai'),
        ('dotenv', 'python-dotenv'),
        ('requests', 'requests')
    ]
    
    missing = []
    import_errors = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError as e:
            print(f"❌ {package_name} is NOT installed")
            missing.append(package_name)
        except Exception as e:
            # Handle other import errors (like Python version compatibility)
            error_msg = str(e)
            if "not subscriptable" in error_msg or "dict[" in error_msg:
                print(f"⚠️  {package_name} requires Python 3.9+ (you have {sys.version_info.major}.{sys.version_info.minor})")
                import_errors.append(package_name)
            else:
                print(f"❌ {package_name} import failed: {error_msg}")
                import_errors.append(package_name)
    
    if import_errors and "atlassian" in str(import_errors):
        print(f"\n⚠️  The atlassian-python-api library requires Python 3.9 or higher")
        print(f"   Your Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print("   Please upgrade Python to 3.9+ or use pyenv/homebrew to install a newer version")
        return False
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"❌ .env file not found!")
        print("   Create it by copying env_template.txt: cp env_template.txt .env")
        return False
    
    print("✅ .env file exists")
    load_dotenv()
    
    required_vars = [
        'CONFLUENCE_URL',
        'CONFLUENCE_USERNAME',
        'CONFLUENCE_API_TOKEN',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
            print(f"❌ {var} is missing")
        elif value == '' or 'your-' in value.lower() or 'example' in value.lower():
            empty_vars.append(var)
            print(f"⚠️  {var} is not configured (still has placeholder value)")
        else:
            # Show only first and last few characters for security
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print(f"✅ {var} is set ({masked})")
    
    if missing_vars or empty_vars:
        print("\n⚠️  Please configure all variables in .env file")
        return False
    
    return True

def check_confluence_connection():
    """Test Confluence connection"""
    try:
        from confluence_connector import ConfluenceConnector
        print("\n🔍 Testing Confluence connection...")
        connector = ConfluenceConnector()
        connector.connect()
        
        # Try to actually get spaces to verify credentials work
        try:
            spaces = connector.get_spaces(limit=1)
            print("✅ Confluence connection successful!")
            print(f"   Connected as: {connector.username}")
            return True
        except Exception as api_error:
            print(f"⚠️  Connection created but API test failed: {str(api_error)}")
            print("   This might indicate:")
            print("   - Incorrect API token")
            print("   - Wrong Confluence URL")
            print("   - Insufficient permissions")
            print("   - Network/firewall issues")
            return False
            
    except Exception as e:
        print(f"❌ Confluence connection failed: {str(e)}")
        print("   Check your credentials in .env file")
        print("   Verify:")
        print("   - CONFLUENCE_URL is correct (should end with /wiki)")
        print("   - CONFLUENCE_USERNAME matches your email")
        print("   - CONFLUENCE_API_TOKEN is valid")
        return False

def check_openai_connection():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  OpenAI API key not found, skipping test")
            return False
        
        print("\n🔍 Testing OpenAI API connection...")
        client = OpenAI(api_key=api_key)
        # Just verify the key format and make a simple call
        models = client.models.list()
        print("✅ OpenAI API connection successful!")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        print("   Check your OPENAI_API_KEY in .env file")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("Confluence Gen AI Agent - Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Checking Python version...")
    results.append(("Python Version", check_python_version()))
    print()
    
    print("2. Checking dependencies...")
    results.append(("Dependencies", check_dependencies()))
    print()
    
    print("3. Checking environment variables...")
    results.append(("Environment Variables", check_env_file()))
    print()
    
    # Only test connections if env vars are set
    if results[-1][1]:
        print("4. Testing connections...")
        confluence_ok = check_confluence_connection()
        openai_ok = check_openai_connection()
        results.append(("Confluence Connection", confluence_ok))
        results.append(("OpenAI Connection", openai_ok))
    
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! You're ready to run the application.")
        print("   Run: python3 main.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("   See SETUP_GUIDE.md for detailed instructions.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
