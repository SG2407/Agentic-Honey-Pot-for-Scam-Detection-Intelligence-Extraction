#!/usr/bin/env python3
"""
Comprehensive Test Suite for Hackathon Organizers
Tests 50+ real-world scenarios with 2-3 message conversations
Mix of scam and legitimate messages
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

DEPLOYED_URL = "https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com"
API_KEY = "team_recursives"

# Test cases with real-world scenarios
TEST_CASES = [
    # ============== BANKING SCAMS (Indian Banks) ==============
    {
        "id": 1,
        "category": "Banking Scam",
        "expected": "scam",
        "messages": [
            "Dear customer, your SBI account has suspicious activity. Verify immediately to avoid blocking.",
            "Share your ATM card number and CVV to verify your identity with SBI security team."
        ]
    },
    {
        "id": 2,
        "category": "Banking Scam",
        "expected": "scam",
        "messages": [
            "HDFC Bank Alert: Unauthorized transaction of Rs 15,000 detected. Call 9876543210 immediately.",
            "Sir, I am calling from HDFC fraud prevention. Share your debit card details to block transaction."
        ]
    },
    {
        "id": 3,
        "category": "Banking Scam",
        "expected": "scam",
        "messages": [
            "ICICI Bank: Your account will be suspended due to non-compliance with KYC norms.",
            "Update your KYC by sharing Aadhaar and PAN card photos on WhatsApp: 9988776655"
        ]
    },
    {
        "id": 4,
        "category": "Banking Scam",
        "expected": "scam",
        "messages": [
            "Axis Bank Security: Multiple failed login attempts detected on your account.",
            "Reset your internet banking password by clicking: http://axis-security-verify.com",
            "Enter your customer ID, DOB and current password to proceed with reset."
        ]
    },
    
    # ============== UPI FRAUD ==============
    {
        "id": 5,
        "category": "UPI Fraud",
        "expected": "scam",
        "messages": [
            "Your UPI payment of Rs 5000 to Amazon has failed. Refund will be processed.",
            "Share your UPI PIN to process refund within 24 hours or amount will be forfeited."
        ]
    },
    {
        "id": 6,
        "category": "UPI Fraud",
        "expected": "scam",
        "messages": [
            "Google Pay: You have received Rs 25,000 cashback! Click to claim.",
            "Enter your UPI ID and verify with 6-digit PIN to receive cashback in your account."
        ]
    },
    {
        "id": 7,
        "category": "UPI Fraud",
        "expected": "scam",
        "messages": [
            "PhonePe KYC Update Required: Complete KYC to continue using PhonePe services.",
            "Share your linked bank account number and UPI PIN for instant KYC verification."
        ]
    },
    
    # ============== OTP/VERIFICATION SCAMS ==============
    {
        "id": 8,
        "category": "OTP Scam",
        "expected": "scam",
        "messages": [
            "You have won Rs 50,000 in Flipkart bumper sale! Claim now.",
            "We sent you OTP on your mobile. Share the OTP to verify and claim your prize money."
        ]
    },
    {
        "id": 9,
        "category": "OTP Scam",
        "expected": "scam",
        "messages": [
            "Your Aadhaar card is linked to 5 bank accounts. This is a security risk.",
            "We will send OTP to de-link unauthorized accounts. Share OTP when you receive it."
        ]
    },
    {
        "id": 10,
        "category": "OTP Scam",
        "expected": "scam",
        "messages": [
            "Urgent: Your mobile number will be disconnected due to non-verification.",
            "Airtel customer care here. Share the OTP we sent to verify your number immediately.",
            "If not verified in 2 hours, your number will be permanently deactivated."
        ]
    },
    
    # ============== PRIZE/LOTTERY SCAMS ==============
    {
        "id": 11,
        "category": "Prize Scam",
        "expected": "scam",
        "messages": [
            "Congratulations! You are selected for Kaun Banega Crorepati Season 15.",
            "Pay registration fee of Rs 5000 via UPI to: kbc-official@paytm to confirm participation."
        ]
    },
    {
        "id": 12,
        "category": "Prize Scam",
        "expected": "scam",
        "messages": [
            "Dear winner, you have won iPhone 15 Pro in our lucky draw contest!",
            "Pay delivery charges Rs 2000 to receive your prize. Share card details for payment."
        ]
    },
    {
        "id": 13,
        "category": "Prize Scam",
        "expected": "scam",
        "messages": [
            "You won Rs 25 lakh in Tata Group anniversary lottery! Claim before it expires.",
            "Contact Mr. Sharma at 9876543210 with your bank details to process prize money."
        ]
    },
    
    # ============== DELIVERY/E-COMMERCE SCAMS ==============
    {
        "id": 14,
        "category": "Delivery Scam",
        "expected": "scam",
        "messages": [
            "Your Amazon package is held due to incomplete address. Update now.",
            "Click here to update address: amazon-delivery-update.com and pay Rs 50 re-delivery fee."
        ]
    },
    {
        "id": 15,
        "category": "Delivery Scam",
        "expected": "scam",
        "messages": [
            "Myntra: Your COD order of Rs 3499 is out for delivery today.",
            "We don't have change. Please share your card details for online payment instead."
        ]
    },
    
    # ============== JOB OFFER SCAMS ==============
    {
        "id": 16,
        "category": "Job Scam",
        "expected": "scam",
        "messages": [
            "Congratulations! You are selected for Google Software Engineer position, salary 25 LPA.",
            "Pay Rs 15000 training fee to confirm your joining. Send payment to secure your position."
        ]
    },
    {
        "id": 17,
        "category": "Job Scam",
        "expected": "scam",
        "messages": [
            "Work from home opportunity! Earn Rs 50,000 per month doing simple data entry.",
            "Registration fee: Rs 5000. Share your bank details to receive work assignments immediately."
        ]
    },
    {
        "id": 18,
        "category": "Job Scam",
        "expected": "scam",
        "messages": [
            "TCS urgent hiring for freshers. Salary 8 LPA. Interview waived for selected candidates.",
            "Pay Rs 10000 documentation fee via UPI to tcs-recruitment@paytm to get offer letter.",
            "Limited seats available. Hurry! Offer valid only for today."
        ]
    },
    
    # ============== INVESTMENT SCAMS ==============
    {
        "id": 19,
        "category": "Investment Scam",
        "expected": "scam",
        "messages": [
            "Invest Rs 10000 today, get Rs 50000 in 30 days. 100% guaranteed returns!",
            "Join our WhatsApp group for exclusive stock tips. Send payment to start earning."
        ]
    },
    {
        "id": 20,
        "category": "Investment Scam",
        "expected": "scam",
        "messages": [
            "Bitcoin investment opportunity! Triple your money in 60 days.",
            "Minimum investment Rs 20000. Share your bank account for direct profit transfer."
        ]
    },
    
    # ============== GOVERNMENT IMPERSONATION ==============
    {
        "id": 21,
        "category": "Government Scam",
        "expected": "scam",
        "messages": [
            "Income Tax Department: You have pending refund of Rs 45000 for FY 2023-24.",
            "Verify your PAN card and bank account details to receive refund within 48 hours."
        ]
    },
    {
        "id": 22,
        "category": "Government Scam",
        "expected": "scam",
        "messages": [
            "UIDAI Notice: Your Aadhaar card is suspended due to multiple registrations.",
            "Update immediately at: uidai-update-portal.in or face legal action and service blockage."
        ]
    },
    {
        "id": 23,
        "category": "Government Scam",
        "expected": "scam",
        "messages": [
            "PM Kisan Yojana: You are eligible for Rs 15000 farmer subsidy payment.",
            "Complete verification by sharing bank passbook photo and Aadhaar to receive amount."
        ]
    },
    
    # ============== TECH SUPPORT SCAMS ==============
    {
        "id": 24,
        "category": "Tech Support Scam",
        "expected": "scam",
        "messages": [
            "Microsoft Security Alert: Your Windows license has expired. Renew immediately.",
            "Call our toll-free support: 1800-MICROSOFT or pay Rs 5000 online for lifetime license."
        ]
    },
    {
        "id": 25,
        "category": "Tech Support Scam",
        "expected": "scam",
        "messages": [
            "Your system is infected with 5 viruses! Immediate action required.",
            "Download our antivirus software from: secure-windows-fix.com and activate with credit card."
        ]
    },
    
    # ============== ROMANCE/SOCIAL SCAMS ==============
    {
        "id": 26,
        "category": "Romance Scam",
        "expected": "scam",
        "messages": [
            "Hi, I'm Sarah from USA. I saw your profile and I think you're very interesting.",
            "I want to send you a gift but customs is asking for Rs 25000 clearance fee. Can you help?",
            "I'll pay you back double when I visit India next month. Share your bank details."
        ]
    },
    
    # ============== ELECTRICITY/UTILITY SCAMS ==============
    {
        "id": 27,
        "category": "Utility Scam",
        "expected": "scam",
        "messages": [
            "MSEB Electricity: Your power will be disconnected in 2 hours due to unpaid bill.",
            "Pay Rs 5450 immediately to avoid disconnection. Pay online: mseb-bill-payment.com"
        ]
    },
    
    # ============== INSURANCE SCAMS ==============
    {
        "id": 28,
        "category": "Insurance Scam",
        "expected": "scam",
        "messages": [
            "LIC policy matured! Claim amount Rs 8 lakh ready for disbursement.",
            "Share your policy number, Aadhaar and bank details to process claim within 24 hours."
        ]
    },
    
    # ============== LEGITIMATE MESSAGES - CASUAL CONVERSATIONS ==============
    {
        "id": 29,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Hey! Are we still on for coffee tomorrow at 5 PM?",
            "Let me know if you need me to pick you up on the way."
        ]
    },
    {
        "id": 30,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Hi, this is Priya from the office. Do you have the Q4 report?",
            "Boss is asking for it. Can you send it by EOD today?"
        ]
    },
    {
        "id": 31,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Mom, I'll be late today. Meeting got extended.",
            "Don't wait for me for dinner. I'll eat outside."
        ]
    },
    {
        "id": 32,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Happy Birthday! Hope you have an amazing day!",
            "Let's celebrate this weekend. Free on Saturday?"
        ]
    },
    {
        "id": 33,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Did you watch the match last night? What a game!",
            "India won by 45 runs. Kohli played brilliantly."
        ]
    },
    {
        "id": 34,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Thanks for your help with the project. Really appreciate it!",
            "Let me know if you need any help from my side too."
        ]
    },
    
    # ============== LEGITIMATE - WORK RELATED ==============
    {
        "id": 35,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Team meeting scheduled for 3 PM today in Conference Room A.",
            "Please bring your laptops. We'll be discussing the new client requirements."
        ]
    },
    {
        "id": 36,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Your leave application for 5th-7th Feb has been approved.",
            "Enjoy your time off! See you on the 8th."
        ]
    },
    {
        "id": 37,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Reminder: Code review session at 11 AM tomorrow.",
            "Please push your latest changes to the dev branch before that."
        ]
    },
    
    # ============== LEGITIMATE - DELIVERY/SHOPPING ==============
    {
        "id": 38,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Your Amazon order #123-4567890-1234567 has been shipped.",
            "Expected delivery: Feb 3. Track your package in the Amazon app."
        ]
    },
    {
        "id": 39,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Flipkart: Your order will be delivered today between 10 AM - 2 PM.",
            "Our delivery executive will call you 30 minutes before arrival."
        ]
    },
    {
        "id": 40,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Swiggy: Your food order from Domino's is out for delivery.",
            "Estimated arrival: 25 minutes. Track your order in the app."
        ]
    },
    
    # ============== LEGITIMATE - BANKING (GENUINE) ==============
    {
        "id": 41,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Your SBI account XXXXXX1234 has been credited with Rs 50,000 on 01-Feb-2026.",
            "Available balance: Rs 75,430. Thank you for banking with us."
        ]
    },
    {
        "id": 42,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "HDFC Bank: Your credit card bill of Rs 12,450 is due on 10-Feb-2026.",
            "Pay online through NetBanking or mobile app to avoid late fees."
        ]
    },
    
    # ============== LEGITIMATE - APPOINTMENTS ==============
    {
        "id": 43,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Appointment reminder: Dr. Sharma, 5th Feb at 4:30 PM.",
            "Address: Apollo Hospital, Pune. Please carry your medical reports."
        ]
    },
    {
        "id": 44,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Your car service appointment is confirmed for 6th Feb at 10 AM.",
            "Maruti Service Center, Wakad. Expected time: 2-3 hours."
        ]
    },
    
    # ============== LEGITIMATE - EDUCATION ==============
    {
        "id": 45,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "University exam schedule released. Check student portal for details.",
            "Mid-semester exams start from 15th Feb. All the best!"
        ]
    },
    {
        "id": 46,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Assignment submission deadline extended to 10th Feb due to technical issues.",
            "Submit your work through the college LMS portal."
        ]
    },
    
    # ============== MORE SCAMS - LOAN SCAMS ==============
    {
        "id": 47,
        "category": "Loan Scam",
        "expected": "scam",
        "messages": [
            "Pre-approved personal loan of Rs 5 lakh at 0% interest! Limited time offer.",
            "Pay Rs 5000 processing fee to get instant loan disbursement in your account."
        ]
    },
    {
        "id": 48,
        "category": "Loan Scam",
        "expected": "scam",
        "messages": [
            "HDFC Bank: You are eligible for education loan of Rs 10 lakh.",
            "Share your Aadhaar, PAN and bank statement to process loan within 24 hours.",
            "Pay Rs 10000 documentation charges via UPI for immediate approval."
        ]
    },
    
    # ============== CHARITY SCAMS ==============
    {
        "id": 49,
        "category": "Charity Scam",
        "expected": "scam",
        "messages": [
            "Help earthquake victims in Turkey! Donate for relief work.",
            "Send donations to UPI: charity-relief@paytm. Every rupee counts!"
        ]
    },
    
    # ============== RENTAL SCAMS ==============
    {
        "id": 50,
        "category": "Rental Scam",
        "expected": "scam",
        "messages": [
            "2BHK apartment available in Baner, Pune. Rent Rs 18000/month.",
            "Pay 3 months advance rent to my account to confirm booking. Flat is in high demand!"
        ]
    },
    
    # ============== ELECTRICITY BILL SCAM ==============
    {
        "id": 51,
        "category": "Utility Scam",
        "expected": "scam",
        "messages": [
            "BSES Alert: Your electricity will be disconnected today due to unpaid dues.",
            "Pay Rs 8550 immediately to avoid disconnection: payment-bses.com"
        ]
    },
    
    # ============== CREDIT CARD SCAMS ==============
    {
        "id": 52,
        "category": "Credit Card Scam",
        "expected": "scam",
        "messages": [
            "Your credit card ending 4567 has been used for Rs 45000 purchase in Dubai.",
            "If this wasn't you, call 1800-245-6789 immediately to block your card.",
            "Share your card CVV and expiry date to cancel this fraudulent transaction."
        ]
    },
    
    # ============== PARCEL/CUSTOMS SCAM ==============
    {
        "id": 53,
        "category": "Customs Scam",
        "expected": "scam",
        "messages": [
            "You have a parcel from UK customs. Pay Rs 5000 customs duty to release.",
            "Parcel contains gift worth Rs 50000. Pay online: customs-clearance-india.com"
        ]
    },
    
    # ============== SOCIAL MEDIA ACCOUNT SCAM ==============
    {
        "id": 54,
        "category": "Social Media Scam",
        "expected": "scam",
        "messages": [
            "Your Instagram account will be deleted due to copyright violation.",
            "Click here to appeal: instagram-appeal-verification.com within 24 hours.",
            "Verify your identity with phone number and OTP to save your account."
        ]
    },
    
    # ============== MORE LEGITIMATE - FAMILY ==============
    {
        "id": 55,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Dad, I've reached the hotel safely. Journey was smooth.",
            "Will call you after freshening up. Love you!"
        ]
    },
    {
        "id": 56,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Don't forget to pick up groceries on your way home.",
            "I've sent you the list on WhatsApp. Need them for dinner tonight."
        ]
    },
    
    # ============== LEGITIMATE - SOCIAL PLANS ==============
    {
        "id": 57,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Movie plan for this weekend? New Marvel movie is out!",
            "Let me know if Saturday evening works. I'll book tickets."
        ]
    },
    {
        "id": 58,
        "category": "Legitimate",
        "expected": "legitimate",
        "messages": [
            "Planning a trip to Goa next month. Are you interested?",
            "Tentative dates: 15-20 March. Let me know so I can make bookings."
        ]
    },
    
    # ============== MORE SCAMS - MOBILE RECHARGE ==============
    {
        "id": 59,
        "category": "Recharge Scam",
        "expected": "scam",
        "messages": [
            "Jio Offer: Get Rs 999 recharge free! Limited to first 1000 users.",
            "Click: jio-free-recharge.com and enter your mobile number and OTP to claim."
        ]
    },
    
    # ============== DUPLICATE SIM SCAM ==============
    {
        "id": 60,
        "category": "SIM Scam",
        "expected": "scam",
        "messages": [
            "Urgent: Someone is trying to get duplicate SIM of your number.",
            "Airtel customer care: Share OTP to block duplicate SIM request immediately.",
            "If you don't respond in 1 hour, duplicate SIM will be issued."
        ]
    }
]

class HackathonOrganiserTest:
    """Comprehensive testing suite for hackathon evaluation"""
    
    def __init__(self):
        self.base_url = DEPLOYED_URL
        self.api_key = API_KEY
        self.results = []
        
    async def test_conversation(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a complete conversation with 2-3 messages"""
        
        test_id = test_case["id"]
        category = test_case["category"]
        expected = test_case["expected"]
        messages = test_case["messages"]
        
        session_id = f"hackathon-test-{test_id}-{int(datetime.now().timestamp())}"
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        conversation_history = []
        detected_as_scam = False
        confidence_scores = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for msg_idx, message_text in enumerate(messages):
                payload = {
                    "sessionId": session_id,
                    "message": {
                        "sender": "user",
                        "text": message_text,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "conversationHistory": conversation_history,
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{self.base_url}/honeypot",
                        headers=headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        scam_detection = result.get('scamDetection', {})
                        
                        if scam_detection.get('isScam', False):
                            detected_as_scam = True
                            
                        confidence_scores.append(scam_detection.get('confidence', 0.0))
                        
                        # Update conversation history
                        conversation_history.append({
                            "sender": "user",
                            "text": message_text,
                            "timestamp": payload["message"]["timestamp"]
                        })
                        conversation_history.append({
                            "sender": "agent",
                            "text": result.get('reply', ''),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        return {
                            "test_id": test_id,
                            "category": category,
                            "expected": expected,
                            "detected": "error",
                            "correct": False,
                            "error": f"HTTP {response.status_code}"
                        }
                        
                except Exception as e:
                    return {
                        "test_id": test_id,
                        "category": category,
                        "expected": expected,
                        "detected": "error",
                        "correct": False,
                        "error": str(e)
                    }
                
                await asyncio.sleep(0.5)  # Small delay between messages
        
        # Determine detection result
        detected = "scam" if detected_as_scam else "legitimate"
        correct = (detected == expected)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "test_id": test_id,
            "category": category,
            "expected": expected,
            "detected": detected,
            "correct": correct,
            "confidence": round(avg_confidence, 2),
            "messages_count": len(messages)
        }
    
    async def run_all_tests(self):
        """Run all test cases"""
        
        print("=" * 80)
        print("🏆 HACKATHON ORGANISER COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"📊 Total Test Cases: {len(TEST_CASES)}")
        print(f"🌐 API Endpoint: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        scam_tests = [tc for tc in TEST_CASES if tc["expected"] == "scam"]
        legit_tests = [tc for tc in TEST_CASES if tc["expected"] == "legitimate"]
        
        print(f"📍 Test Distribution:")
        print(f"   🚨 Scam Messages: {len(scam_tests)}")
        print(f"   ✅ Legitimate Messages: {len(legit_tests)}")
        print()
        print("🔄 Running tests... (this will take a few minutes)")
        print("-" * 80)
        
        for i, test_case in enumerate(TEST_CASES, 1):
            result = await self.test_conversation(test_case)
            self.results.append(result)
            
            status_icon = "✅" if result['correct'] else "❌"
            print(f"{status_icon} Test {i:2d}/{len(TEST_CASES)} | "
                  f"{test_case['category']:20s} | "
                  f"Expected: {result['expected']:10s} | "
                  f"Detected: {result['detected']:10s} | "
                  f"{'PASS' if result['correct'] else 'FAIL'}")
        
        print()
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        print()
        
        # Overall Statistics
        total_tests = len(self.results)
        correct_tests = sum(1 for r in self.results if r['correct'])
        incorrect_tests = total_tests - correct_tests
        accuracy = (correct_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("🎯 OVERALL PERFORMANCE:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Correct: {correct_tests}")
        print(f"   ❌ Incorrect: {incorrect_tests}")
        print(f"   📈 Accuracy: {accuracy:.2f}%")
        print()
        
        # Scam Detection Performance
        scam_results = [r for r in self.results if r['expected'] == 'scam']
        scam_correct = sum(1 for r in scam_results if r['correct'])
        scam_accuracy = (scam_correct / len(scam_results) * 100) if scam_results else 0
        
        print("🚨 SCAM DETECTION PERFORMANCE:")
        print(f"   Total Scam Tests: {len(scam_results)}")
        print(f"   ✅ Correctly Detected: {scam_correct}")
        print(f"   ❌ Missed (False Negatives): {len(scam_results) - scam_correct}")
        print(f"   📈 Scam Detection Rate: {scam_accuracy:.2f}%")
        print()
        
        # Legitimate Message Performance
        legit_results = [r for r in self.results if r['expected'] == 'legitimate']
        legit_correct = sum(1 for r in legit_results if r['correct'])
        legit_accuracy = (legit_correct / len(legit_results) * 100) if legit_results else 0
        false_positives = len(legit_results) - legit_correct
        
        print("✅ LEGITIMATE MESSAGE PERFORMANCE:")
        print(f"   Total Legitimate Tests: {len(legit_results)}")
        print(f"   ✅ Correctly Identified: {legit_correct}")
        print(f"   ❌ False Positives: {false_positives}")
        print(f"   📈 Legitimate Detection Rate: {legit_accuracy:.2f}%")
        print()
        
        # Category-wise Breakdown
        print("📂 CATEGORY-WISE PERFORMANCE:")
        print("-" * 80)
        
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'correct': 0}
            categories[cat]['total'] += 1
            if result['correct']:
                categories[cat]['correct'] += 1
        
        for cat, stats in sorted(categories.items()):
            cat_accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if cat_accuracy >= 80 else "⚠️" if cat_accuracy >= 60 else "❌"
            print(f"   {status} {cat:25s}: {stats['correct']:2d}/{stats['total']:2d} ({cat_accuracy:5.1f}%)")
        
        print()
        
        # Failed Test Cases
        failed_tests = [r for r in self.results if not r['correct']]
        if failed_tests:
            print("❌ FAILED TEST CASES (Need Improvement):")
            print("-" * 80)
            for fail in failed_tests:
                print(f"   Test #{fail['test_id']:2d} | {fail['category']:20s} | "
                      f"Expected: {fail['expected']:10s} but got {fail['detected']:10s}")
            print()
        
        # Confidence Analysis
        avg_confidence = sum(r.get('confidence', 0) for r in self.results) / len(self.results)
        print(f"📊 AVERAGE CONFIDENCE SCORE: {avg_confidence:.2f}")
        print()
        
        # Final Verdict
        print("=" * 80)
        print("🏆 FINAL VERDICT:")
        print("=" * 80)
        
        if accuracy >= 95:
            verdict = "EXCELLENT ⭐⭐⭐⭐⭐"
            comment = "Outstanding performance! System is production-ready."
        elif accuracy >= 90:
            verdict = "VERY GOOD ⭐⭐⭐⭐"
            comment = "Strong performance with minor room for improvement."
        elif accuracy >= 80:
            verdict = "GOOD ⭐⭐⭐"
            comment = "Good performance but needs refinement."
        elif accuracy >= 70:
            verdict = "ACCEPTABLE ⭐⭐"
            comment = "Acceptable but significant improvements needed."
        else:
            verdict = "NEEDS IMPROVEMENT ⭐"
            comment = "Major improvements required before deployment."
        
        print(f"   {verdict}")
        print(f"   {comment}")
        print()
        
        if false_positives > 0:
            print(f"   ⚠️  Warning: {false_positives} false positives detected.")
            print(f"      Legitimate users may be incorrectly flagged.")
        
        if len(scam_results) - scam_correct > 0:
            print(f"   ⚠️  Warning: {len(scam_results) - scam_correct} scams missed.")
            print(f"      Some scam attempts may go undetected.")
        
        print()
        print("=" * 80)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Save results to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'correct': correct_tests,
                    'incorrect': incorrect_tests,
                    'accuracy': accuracy,
                    'scam_detection_rate': scam_accuracy,
                    'legitimate_detection_rate': legit_accuracy,
                    'false_positives': false_positives,
                    'false_negatives': len(scam_results) - scam_correct
                },
                'detailed_results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

async def main():
    """Main function"""
    tester = HackathonOrganiserTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
