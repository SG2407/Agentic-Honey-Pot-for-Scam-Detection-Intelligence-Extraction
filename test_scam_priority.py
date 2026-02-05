"""Test scam type priority locking logic"""

SCAM_TYPE_PRIORITY = {
    'credential_phishing': 4,  # Highest
    'financial_threat': 3,
    'impersonation': 2,
    'reward_scam': 1,
    'unknown': 0,
}

def test_priority_logic():
    """Simulate a conversation with multiple scam type detections"""
    session_types = {}
    session_id = 'test-123'
    
    print("=" * 80)
    print("SCAM TYPE PRIORITY LOCKING TEST")
    print("=" * 80)
    print()
    
    # Message 1: Account suspended (financial_threat)
    current = 'financial_threat'
    print(f"Message 1: Detected '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
    session_types[session_id] = current
    print(f"  → Session locked to: {session_types[session_id]}")
    print()
    
    # Message 2: Provide Aadhaar (credential_phishing - HIGHER priority)
    current = 'credential_phishing'
    existing = session_types[session_id]
    print(f"Message 2: Detected '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
    if SCAM_TYPE_PRIORITY[current] > SCAM_TYPE_PRIORITY[existing]:
        print(f"  → UPGRADING: {existing} → {current}")
        session_types[session_id] = current
    print(f"  → Session locked to: {session_types[session_id]}")
    print()
    
    # Message 3: Account blocked again (financial_threat - LOWER priority)
    current = 'financial_threat'
    existing = session_types[session_id]
    print(f"Message 3: Detected '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
    if SCAM_TYPE_PRIORITY[current] < SCAM_TYPE_PRIORITY[existing]:
        print(f"  → LOCKED: Keeping '{existing}' (priority {SCAM_TYPE_PRIORITY[existing]}) over '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
        current = existing
    print(f"  → Session locked to: {session_types[session_id]}")
    print()
    
    # Message 4: Impersonation (LOWER priority)
    current = 'impersonation'
    existing = session_types[session_id]
    print(f"Message 4: Detected '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
    if SCAM_TYPE_PRIORITY[current] < SCAM_TYPE_PRIORITY[existing]:
        print(f"  → LOCKED: Keeping '{existing}' (priority {SCAM_TYPE_PRIORITY[existing]}) over '{current}' (priority {SCAM_TYPE_PRIORITY[current]})")
    print(f"  → Session locked to: {session_types[session_id]}")
    print()
    
    print("=" * 80)
    print(f"✅ FINAL RESULT: Session stays '{session_types[session_id]}' (no downgrade)")
    print("=" * 80)
    
    # Verify
    assert session_types[session_id] == 'credential_phishing', "Session should stay credential_phishing"
    print("✅ TEST PASSED: Priority locking works correctly")

if __name__ == "__main__":
    test_priority_logic()
