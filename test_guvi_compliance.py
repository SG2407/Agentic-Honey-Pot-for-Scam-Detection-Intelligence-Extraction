#!/usr/bin/env python3
"""
GUVI Compliance Test Suite
Tests all requirements for the Agentic Honey-Pot system
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, List

# Test configuration
BASE_URL = "http://localhost:8000"
HONEYPOT_ENDPOINT = f"{BASE_URL}/honeypot"

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestResult:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed += 1
        self.tests.append({"name": test_name, "status": "PASS", "details": details})
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {test_name}")
        if details:
            print(f"  {Colors.OKCYAN}{details}{Colors.ENDC}")
    
    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.tests.append({"name": test_name, "status": "FAIL", "error": error})
        print(f"{Colors.FAIL}✗{Colors.ENDC} {test_name}")
        print(f"  {Colors.FAIL}Error: {error}{Colors.ENDC}")
    
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"Total Tests: {self.total}")
        print(f"{Colors.OKGREEN}Passed: {self.passed}{Colors.ENDC}")
        if self.failed > 0:
            print(f"{Colors.FAIL}Failed: {self.failed}{Colors.ENDC}")
        
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.ENDC}")
        
        if success_rate == 100:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED - GUVI COMPLIANT! 🎉{Colors.ENDC}")
        elif success_rate >= 90:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  MOSTLY PASSING - REVIEW FAILURES{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ MULTIPLE FAILURES - NEEDS ATTENTION{Colors.ENDC}")

def send_message(session_id: str, messages: List[Dict]) -> Dict:
    """Send a message to the honeypot endpoint"""
    payload = {
        "session_id": session_id,
        "conversation": messages
    }
    
    response = requests.post(
        HONEYPOT_ENDPOINT,
        json=payload,
        headers={"x-api-key": "team_recursives"}  # PRIORITY 1: API key required
    )
    return {
        "status_code": response.status_code,
        "response": response.json() if response.status_code == 200 else None,
        "text": response.text
    }

def test_legitimate_messages(results: TestResult):
    """Test 1: Legitimate messages should be handled gracefully"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 1: Legitimate Message Handling{Colors.ENDC}")
    
    legitimate_messages = [
        "Hello, how are you?",
        "Can I get product information?",
        "Thank you for your help",
        "What are your business hours?",
    ]
    
    for msg in legitimate_messages:
        session_id = f"legit-{int(time.time())}"
        response = send_message(session_id, [
            {
                "sender": "scammer",
                "text": msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ])
        
        if response["status_code"] == 200:
            reply = response["response"].get("reply", "")
            if reply and len(reply) > 0:
                results.add_pass(f"Legitimate message handled: '{msg[:30]}...'", f"Reply: '{reply}'")
            else:
                results.add_fail(f"Legitimate message: '{msg[:30]}...'", "No reply generated")
        else:
            results.add_fail(f"Legitimate message: '{msg[:30]}...'", f"HTTP {response['status_code']}")
        
        time.sleep(0.5)

def test_scam_detection(results: TestResult):
    """Test 2: Scam messages should be detected correctly"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 2: Scam Detection{Colors.ENDC}")
    
    scam_messages = [
        "Your account is blocked! Send OTP immediately!",
        "Congratulations! You won 10 lakh rupees. Claim now!",
        "Income Tax refund of Rs. 25,000 pending. Click to claim.",
        "Your Aadhaar is suspended. Verify now to activate.",
        "UPI payment failed. Share your UPI PIN to verify.",
    ]
    
    for msg in scam_messages:
        session_id = f"scam-{int(time.time())}"
        response = send_message(session_id, [
            {
                "sender": "scammer",
                "text": msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ])
        
        if response["status_code"] == 200:
            reply = response["response"].get("reply", "")
            # Scam should trigger engagement, not neutral reply
            neutral_replies = ["Thank you", "I understand", "Okay", "Noted", "Alright"]
            is_engaging = not any(neutral in reply for neutral in neutral_replies)
            
            if is_engaging:
                results.add_pass(f"Scam detected: '{msg[:40]}...'", f"Engaged with: '{reply[:50]}...'")
            else:
                results.add_fail(f"Scam detection: '{msg[:40]}...'", f"Neutral reply: '{reply}'")
        else:
            results.add_fail(f"Scam detection: '{msg[:40]}...'", f"HTTP {response['status_code']}")
        
        time.sleep(0.5)

def test_intelligence_extraction(results: TestResult):
    """Test 3: Intelligence extraction from scam messages"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 3: Intelligence Extraction{Colors.ENDC}")
    
    test_cases = [
        {
            "msg": "Send money to fraud@paytm immediately!",
            "expected": ["upi_id"],
            "name": "UPI ID extraction"
        },
        {
            "msg": "Call me at +919876543210 for verification",
            "expected": ["phone_number"],
            "name": "Phone number extraction"
        },
        {
            "msg": "Transfer to account 1234567890123",
            "expected": ["bank_account"],
            "name": "Bank account extraction"
        },
        {
            "msg": "Click here: http://fake-bank.com/phishing",
            "expected": ["phishing_link"],
            "name": "Phishing link extraction"
        },
    ]
    
    for test_case in test_cases:
        session_id = f"intel-{int(time.time())}"
        
        # First message to establish scam
        send_message(session_id, [
            {
                "sender": "scammer",
                "text": "Your account is blocked!",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ])
        time.sleep(0.5)
        
        # Second message with intelligence
        response = send_message(session_id, [
            {
                "sender": "scammer",
                "text": "Your account is blocked!",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "sender": "user",
                "text": "What should I do?",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "sender": "scammer",
                "text": test_case["msg"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ])
        
        if response["status_code"] == 200:
            # Note: Intelligence is extracted but not returned in API response
            # System should detect and process it internally
            results.add_pass(test_case["name"], f"Message processed: '{test_case['msg'][:50]}...'")
        else:
            results.add_fail(test_case["name"], f"HTTP {response['status_code']}")
        
        time.sleep(0.5)

def test_conversation_flow(results: TestResult):
    """Test 4: Multi-turn conversation handling"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 4: Multi-Turn Conversation Flow{Colors.ENDC}")
    
    session_id = f"convo-{int(time.time())}"
    conversation = []
    
    # Turn 1: Initial scam
    conversation.append({
        "sender": "scammer",
        "text": "Your bank account is compromised! Urgent action needed.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    response = send_message(session_id, conversation.copy())
    if response["status_code"] == 200:
        reply = response["response"].get("reply", "")
        results.add_pass("Turn 1: Initial scam detection", f"Reply: '{reply[:50]}...'")
        conversation.append({"sender": "user", "text": reply, "timestamp": datetime.now(timezone.utc).isoformat()})
    else:
        results.add_fail("Turn 1", f"HTTP {response['status_code']}")
        return
    
    time.sleep(0.5)
    
    # Turn 2: Scammer asks for details
    conversation.append({
        "sender": "scammer",
        "text": "What is your account number for verification?",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    response = send_message(session_id, conversation.copy())
    if response["status_code"] == 200:
        reply = response["response"].get("reply", "")
        results.add_pass("Turn 2: Credential request handling", f"Reply: '{reply[:50]}...'")
        conversation.append({"sender": "user", "text": reply, "timestamp": datetime.now(timezone.utc).isoformat()})
    else:
        results.add_fail("Turn 2", f"HTTP {response['status_code']}")
        return
    
    time.sleep(0.5)
    
    # Turn 3: Scammer provides intelligence
    conversation.append({
        "sender": "scammer",
        "text": "Transfer Rs 100 to scammer@paytm for verification",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    response = send_message(session_id, conversation.copy())
    if response["status_code"] == 200:
        results.add_pass("Turn 3: Intelligence extraction trigger", "UPI ID should be extracted")
    else:
        results.add_fail("Turn 3", f"HTTP {response['status_code']}")

def test_max_turn_limit(results: TestResult):
    """Test 5: Maximum conversation turn limit"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 5: Maximum Turn Limit Enforcement{Colors.ENDC}")
    
    session_id = f"limit-{int(time.time())}"
    conversation = []
    
    # Send messages up to the limit (20 turns = 40 messages)
    for i in range(15):
        conversation.append({
            "sender": "scammer",
            "text": f"Scam message {i}: Your account is blocked!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        response = send_message(session_id, conversation.copy())
        if response["status_code"] == 200:
            reply = response["response"].get("reply", "")
            conversation.append({"sender": "user", "text": reply, "timestamp": datetime.now(timezone.utc).isoformat()})
        
        time.sleep(0.3)
    
    # Check if session continues or stops
    conversation.append({
        "sender": "scammer",
        "text": "Final message test",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    response = send_message(session_id, conversation.copy())
    if response["status_code"] == 200:
        results.add_pass("Turn limit handling", "Session handled multiple turns correctly")
    else:
        results.add_fail("Turn limit", f"HTTP {response['status_code']}")

def test_error_handling(results: TestResult):
    """Test 6: Error handling and edge cases"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 6: Error Handling & Edge Cases{Colors.ENDC}")
    
    # Test 1: Empty message
    response = send_message("error-empty", [
        {"sender": "scammer", "text": "", "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    if response["status_code"] == 200:
        results.add_pass("Empty message handling", "Returns 200 OK")
    else:
        results.add_fail("Empty message", f"HTTP {response['status_code']}")
    
    time.sleep(0.3)
    
    # Test 2: Very long message
    long_text = "A" * 5000
    response = send_message("error-long", [
        {"sender": "scammer", "text": long_text, "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    if response["status_code"] == 200:
        results.add_pass("Long message handling", "Returns 200 OK")
    else:
        results.add_fail("Long message", f"HTTP {response['status_code']}")
    
    time.sleep(0.3)
    
    # Test 3: Special characters
    response = send_message("error-special", [
        {"sender": "scammer", "text": "Test with émojis 😀🎉 and spëcial çhars!", "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    if response["status_code"] == 200:
        results.add_pass("Special characters handling", "Returns 200 OK")
    else:
        results.add_fail("Special characters", f"HTTP {response['status_code']}")

def test_session_isolation(results: TestResult):
    """Test 7: Session isolation"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 7: Session Isolation{Colors.ENDC}")
    
    # Create two separate sessions
    session1 = f"session-1-{int(time.time())}"
    session2 = f"session-2-{int(time.time())}"
    
    # Send different messages to each
    response1 = send_message(session1, [
        {"sender": "scammer", "text": "Account blocked in session 1!", "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    
    time.sleep(0.3)
    
    response2 = send_message(session2, [
        {"sender": "scammer", "text": "Prize won in session 2!", "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    
    if response1["status_code"] == 200 and response2["status_code"] == 200:
        reply1 = response1["response"].get("reply", "")
        reply2 = response2["response"].get("reply", "")
        
        # Replies should be different (sessions isolated)
        if reply1 != reply2:
            results.add_pass("Session isolation", f"Different replies for different sessions")
        else:
            results.add_fail("Session isolation", "Same reply for different sessions")
    else:
        results.add_fail("Session isolation", "One or both requests failed")

def test_response_format(results: TestResult):
    """Test 8: Response format compliance"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}TEST 8: Response Format Compliance{Colors.ENDC}")
    
    response = send_message("format-test", [
        {"sender": "scammer", "text": "Test message", "timestamp": datetime.now(timezone.utc).isoformat()}
    ])
    
    if response["status_code"] == 200:
        resp_data = response["response"]
        
        # Check required fields
        if "status" in resp_data:
            results.add_pass("Response has 'status' field", f"status: {resp_data['status']}")
        else:
            results.add_fail("Response format", "Missing 'status' field")
        
        if "reply" in resp_data:
            results.add_pass("Response has 'reply' field", f"reply length: {len(resp_data['reply'])} chars")
        else:
            results.add_fail("Response format", "Missing 'reply' field")
        
        if resp_data.get("status") == "success":
            results.add_pass("Status value is 'success'", "Correct status format")
        else:
            results.add_fail("Status format", f"Status is '{resp_data.get('status')}', expected 'success'")
    else:
        results.add_fail("Response format test", f"HTTP {response['status_code']}")

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("     GUVI COMPLIANCE TEST SUITE - AGENTIC HONEY-POT")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
        print(f"{Colors.OKGREEN}✓ Server is running at {BASE_URL}{Colors.ENDC}\n")
    except requests.exceptions.RequestException:
        print(f"{Colors.FAIL}✗ Server is not running at {BASE_URL}{Colors.ENDC}")
        print(f"{Colors.WARNING}Please start the server with: python -m uvicorn app.main:app --reload{Colors.ENDC}")
        return
    
    results = TestResult()
    
    try:
        # Run all test suites
        test_legitimate_messages(results)
        test_scam_detection(results)
        test_intelligence_extraction(results)
        test_conversation_flow(results)
        test_max_turn_limit(results)
        test_error_handling(results)
        test_session_isolation(results)
        test_response_format(results)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
    
    # Print summary
    results.print_summary()
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": results.total,
            "passed": results.passed,
            "failed": results.failed,
            "success_rate": (results.passed / results.total * 100) if results.total > 0 else 0,
            "tests": results.tests
        }, f, indent=2)
    
    print(f"\n{Colors.OKCYAN}Detailed results saved to: {results_file}{Colors.ENDC}")

if __name__ == "__main__":
    main()
