"""
Simple test script to verify UI components
Run: python ui/test_ui_components.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from ui.session_store import SessionStore
        print("  ✅ session_store imported")
    except Exception as e:
        print(f"  ❌ session_store failed: {e}")
        return False
    
    try:
        from ui.intelligence_monitor import IntelligenceMonitor
        print("  ✅ intelligence_monitor imported")
    except Exception as e:
        print(f"  ❌ intelligence_monitor failed: {e}")
        return False
    
    try:
        import fastapi
        print("  ✅ fastapi available")
    except Exception as e:
        print(f"  ❌ fastapi not installed: {e}")
        return False
    
    try:
        import streamlit
        print("  ✅ streamlit available")
    except Exception as e:
        print(f"  ❌ streamlit not installed: {e}")
        return False
    
    return True

def test_session_store():
    """Test SessionStore functionality"""
    print("\n📦 Testing SessionStore...")
    
    try:
        from ui.session_store import SessionStore
        
        # Create test store
        store = SessionStore(db_path="ui/test_sessions.db")
        
        # Create session
        session = store.create_session("test-123")
        print(f"  ✅ Created session: {session['session_id']}")
        
        # Add message
        store.add_message("test-123", "scammer", "Test message", 12345)
        print("  ✅ Added message")
        
        # Get history
        history = store.get_conversation_history("test-123")
        assert len(history) == 1, "Message not stored"
        print("  ✅ Retrieved conversation history")
        
        # Update intelligence
        intel = {
            "bankAccounts": ["123456789"],
            "upiIds": ["test@upi"],
            "phoneNumbers": [],
            "phishingLinks": [],
            "suspiciousKeywords": ["urgent"]
        }
        store.update_intelligence("test-123", intel)
        print("  ✅ Updated intelligence")
        
        # Get session
        session = store.get_session("test-123")
        assert session["intelligence"]["bankAccounts"][0] == "123456789"
        print("  ✅ Intelligence stored correctly")
        
        # Cleanup
        store.delete_session("test-123")
        print("  ✅ Deleted test session")
        
        # Remove test database
        if os.path.exists("ui/test_sessions.db"):
            os.remove("ui/test_sessions.db")
        
        return True
        
    except Exception as e:
        print(f"  ❌ SessionStore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligence_monitor():
    """Test IntelligenceMonitor functionality"""
    print("\n🧠 Testing IntelligenceMonitor...")
    
    try:
        from ui.intelligence_monitor import IntelligenceMonitor
        
        monitor = IntelligenceMonitor()
        
        # Test intelligence extraction
        message = "Your account 123456789 is blocked! Call +91-9876543210 or pay via scammer@upi"
        intel = monitor.extract_intelligence(message, [])
        
        assert len(intel["bankAccounts"]) > 0, "Bank account not detected"
        print(f"  ✅ Detected bank accounts: {intel['bankAccounts']}")
        
        assert len(intel["phoneNumbers"]) > 0, "Phone not detected"
        print(f"  ✅ Detected phone numbers: {intel['phoneNumbers']}")
        
        assert len(intel["upiIds"]) > 0, "UPI not detected"
        print(f"  ✅ Detected UPI IDs: {intel['upiIds']}")
        
        # Test scam detection
        scam_info = monitor.detect_scam(message, [])
        assert scam_info["is_scam"], "Scam not detected"
        print(f"  ✅ Detected scam: {scam_info['scam_type']} ({scam_info['confidence']})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ IntelligenceMonitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """Test environment configuration"""
    print("\n⚙️  Testing environment...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv("ui/.env.ui")
        print("  ✅ Environment file loaded")
        
        api_url = os.getenv("HONEYPOT_API_URL")
        if api_url:
            print(f"  ✅ HONEYPOT_API_URL: {api_url}")
        else:
            print("  ⚠️  HONEYPOT_API_URL not set (will use default)")
        
        api_key = os.getenv("API_KEY")
        if api_key:
            print(f"  ✅ API_KEY: {api_key[:4]}...{api_key[-4:]}")
        else:
            print("  ⚠️  API_KEY not set (will use default)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Environment test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 UI Components Test Suite")
    print("=" * 50)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("SessionStore", test_session_store()))
    results.append(("IntelligenceMonitor", test_intelligence_monitor()))
    results.append(("Environment", test_environment()))
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! UI is ready to use.")
        print("\n🚀 Start the UI with:")
        print("   cd ui && ./start_ui.sh")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
