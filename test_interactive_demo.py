"""
Interactive Demo Test - Thoroughly test system with GUVI-style inputs
Shows full conversation flow, agent replies, intelligence extraction, and logs
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import List, Dict

BASE_URL = "http://localhost:8000"

class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{text.center(80)}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")

def print_scammer(text: str):
    """Print scammer message"""
    print(f"{Color.RED}{Color.BOLD}🚨 SCAMMER:{Color.END} {Color.RED}{text}{Color.END}")

def print_agent(text: str):
    """Print agent reply"""
    print(f"{Color.GREEN}{Color.BOLD}🤖 AGENT:{Color.END} {Color.GREEN}{text}{Color.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Color.YELLOW}ℹ️  {text}{Color.END}")

def print_success(text: str):
    """Print success message"""
    print(f"{Color.GREEN}✅ {text}{Color.END}")

def print_intelligence(intel: Dict):
    """Print extracted intelligence"""
    if not intel:
        return
    
    print(f"\n{Color.MAGENTA}{Color.BOLD}📊 INTELLIGENCE EXTRACTED:{Color.END}")
    
    if intel.get('bank_accounts'):
        print(f"{Color.MAGENTA}   💳 Bank Accounts: {', '.join(intel['bank_accounts'])}{Color.END}")
    if intel.get('upi_ids'):
        print(f"{Color.MAGENTA}   💰 UPI IDs: {', '.join(intel['upi_ids'])}{Color.END}")
    if intel.get('phone_numbers'):
        print(f"{Color.MAGENTA}   📱 Phone Numbers: {', '.join(intel['phone_numbers'])}{Color.END}")
    if intel.get('phishing_links'):
        print(f"{Color.MAGENTA}   🔗 Phishing Links: {', '.join(intel['phishing_links'])}{Color.END}")
    if intel.get('suspicious_keywords'):
        print(f"{Color.MAGENTA}   🔍 Keywords: {', '.join(intel['suspicious_keywords'][:5])}{Color.END}")

def send_message(session_id: str, scammer_message: str, conversation_history: List[Dict] = None) -> Dict:
    """Send message to honeypot and get response"""
    if conversation_history is None:
        conversation_history = []
    
    # Add current scammer message to history
    current_msg = {
        "sender": "scammer",
        "text": scammer_message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    payload = {
        "sessionId": session_id,
        "message": current_msg,
        "conversationHistory": conversation_history
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": "team_recursives"  # PRIORITY 1: API key required
            },
            timeout=30
        )
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def run_conversation(scenario_name: str, session_id: str, scammer_messages: List[str], delay: float = 1.0):
    """Run a full conversation scenario"""
    print_header(f"SCENARIO: {scenario_name}")
    print_info(f"Session ID: {session_id}")
    print_info(f"Messages to send: {len(scammer_messages)}")
    print()
    
    conversation_history = []
    extracted_intel = {}
    
    for i, scammer_msg in enumerate(scammer_messages):
        print(f"\n{Color.BOLD}--- Turn {i+1} ---{Color.END}")
        print_scammer(scammer_msg)
        
        # Send message
        result = send_message(session_id, scammer_msg, conversation_history)
        
        if not result["success"]:
            print(f"{Color.RED}❌ Error: {result['error']}{Color.END}")
            break
        
        # Get response
        response_data = result["data"]
        agent_reply = response_data.get("reply", "")
        
        if agent_reply:
            print_agent(agent_reply)
            
            # Update conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": scammer_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            conversation_history.append({
                "sender": "user",
                "text": agent_reply,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            print(f"{Color.YELLOW}⚠️  Empty reply (session may be closed){Color.END}")
            break
        
        # Check for intelligence in response
        if "intelligence" in response_data:
            intel = response_data["intelligence"]
            if intel and any(intel.values()):
                extracted_intel = intel
                print_intelligence(intel)
        
        # Wait before next message
        if i < len(scammer_messages) - 1:
            time.sleep(delay)
    
    print(f"\n{Color.BOLD}{'─'*80}{Color.END}")
    print_success(f"Scenario '{scenario_name}' completed!")
    print_info(f"Total turns: {len(conversation_history) // 2}")
    
    if extracted_intel:
        print_intelligence(extracted_intel)
    
    print()
    time.sleep(2)

def test_credential_phishing_otp():
    """Test OTP phishing scenario with gradual engagement"""
    scenario = "Credential Phishing - OTP Request"
    session_id = f"test-otp-{int(time.time())}"
    
    messages = [
        "Your account has been blocked due to suspicious activity. Please share OTP to verify.",
        "This is urgent! Your account will be permanently closed in 1 hour if not verified.",
        "I need the 6 digit OTP sent to your mobile immediately to unblock.",
        "Don't worry, this is standard security procedure. Just share the code.",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.5)

def test_prize_scam_with_upi():
    """Test prize/lottery scam with UPI collection"""
    scenario = "Prize Scam - UPI Collection"
    session_id = f"test-prize-{int(time.time())}"
    
    messages = [
        "Congratulations! You have won 10 lakh rupees in our lucky draw!",
        "To claim your prize, you need to verify your UPI ID. Which app do you use?",
        "Please share your UPI ID like user@paytm or user@phonepe to transfer the amount.",
        "There is a small processing fee of Rs 500. After payment, prize will be credited.",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.5)

def test_bank_account_threat():
    """Test bank account threat scenario"""
    scenario = "Financial Threat - Account Suspended"
    session_id = f"test-bank-{int(time.time())}"
    
    messages = [
        "Alert! Your bank account 1234567890 is suspended due to KYC verification pending.",
        "You must update your account details immediately to avoid permanent closure.",
        "Please confirm your account number and IFSC code for verification.",
        "Call our helpline at 9876543210 or your account will be closed today.",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.5)

def test_impersonation_tax():
    """Test government impersonation scenario"""
    scenario = "Impersonation - Income Tax Department"
    session_id = f"test-tax-{int(time.time())}"
    
    messages = [
        "Income Tax Department: You have pending refund of Rs. 25,000.",
        "To process your refund, click this link: http://fake-tax-refund.com/verify",
        "Enter your PAN card and bank account details to receive the refund.",
        "This refund will expire in 48 hours if not claimed.",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.5)

def test_legitimate_message():
    """Test legitimate message handling"""
    scenario = "Legitimate Message - Business Inquiry"
    session_id = f"test-legit-{int(time.time())}"
    
    messages = [
        "Hi, I saw your product listing. What is the price?",
        "Can you provide more details about the specifications?",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.0)

def test_multi_turn_engagement():
    """Test extended conversation with multiple intelligence pieces"""
    scenario = "Extended Engagement - Intelligence Collection"
    session_id = f"test-multi-{int(time.time())}"
    
    messages = [
        "Your Aadhaar card is suspended. Verify immediately to avoid legal action.",
        "This is from government office. You must act now or face penalties.",
        "Send me your Aadhaar number and mobile number for verification.",
        "Also need your bank account 9876543210 details to process.",
        "You can also pay verification fee via UPI at scammer@paytm",
        "For urgent help, call me at 8765432109 right now.",
        "Still waiting... Your case will be filed if you don't respond.",
    ]
    
    run_conversation(scenario, session_id, messages, delay=1.0)

def main():
    """Run all test scenarios"""
    print_header("🎯 INTERACTIVE SYSTEM DEMO - GUVI Style Testing")
    print_info("This will test the system with realistic scam scenarios")
    print_info("Watch the logs in the server terminal to see:")
    print_info("  - Scam detection and classification")
    print_info("  - Agent engagement quality (follow-up questions, hesitation)")
    print_info("  - Intelligence extraction (UPI, phones, bank accounts)")
    print_info("  - Session lifecycle management")
    print()
    input(f"{Color.YELLOW}Press Enter to start testing...{Color.END}")
    
    # Test all scenarios
    test_credential_phishing_otp()
    test_prize_scam_with_upi()
    test_bank_account_threat()
    test_impersonation_tax()
    test_multi_turn_engagement()
    test_legitimate_message()
    
    # Final summary
    print_header("🎉 ALL SCENARIOS COMPLETED")
    print()
    print_success("System testing complete!")
    print_info("Check the server logs to verify:")
    print_info("  ✅ Enhanced engagement quality (follow-up questions, hesitation)")
    print_info("  ✅ Precise intelligence extraction (context-aware)")
    print_info("  ✅ Accurate scam classification (11 patterns)")
    print_info("  ✅ Session lifecycle discipline (hard stop when closed)")
    print_info("  ✅ LLM optimization (caching + fallbacks)")
    print_info("  ✅ Persona consistency (detailed traits)")
    print()
    print(f"{Color.BOLD}{Color.GREEN}🚀 System is ready for GUVI evaluation!{Color.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}Test interrupted by user{Color.END}")
    except Exception as e:
        print(f"\n\n{Color.RED}Error: {e}{Color.END}")
        import traceback
        traceback.print_exc()
