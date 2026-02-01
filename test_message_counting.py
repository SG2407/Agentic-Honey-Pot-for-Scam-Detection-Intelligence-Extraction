"""Test explicit message counting logic"""

print("🧪 Testing Explicit Message Counting\n")
print("="*80)

# Simulate message counting like the actual implementation
message_counts = {}

def receive_scammer_message(session_id):
    """Simulate receiving a scammer message"""
    if session_id not in message_counts:
        message_counts[session_id] = 0
    message_counts[session_id] += 1
    return message_counts[session_id]

def send_agent_reply(session_id):
    """Simulate sending an agent reply"""
    message_counts[session_id] += 1
    return message_counts[session_id]

# Test Scenario 1: First message exchange
print("\n✅ TEST 1: First Message Exchange")
print("-"*80)
session1 = "test-001"
count = receive_scammer_message(session1)
print(f"Step 1: Received scammer message → Count: {count}")
assert count == 1, f"Expected 1, got {count}"

count = send_agent_reply(session1)
print(f"Step 2: Sent agent reply → Count: {count}")
assert count == 2, f"Expected 2, got {count}"
print("✓ PASSED - First exchange: 2 messages total")

# Test Scenario 2: Second message exchange
print("\n✅ TEST 2: Second Message Exchange (Same Session)")
print("-"*80)
count = receive_scammer_message(session1)
print(f"Step 3: Received scammer message → Count: {count}")
assert count == 3, f"Expected 3, got {count}"

count = send_agent_reply(session1)
print(f"Step 4: Sent agent reply → Count: {count}")
assert count == 4, f"Expected 4, got {count}"
print("✓ PASSED - After 2 exchanges: 4 messages total")

# Test Scenario 3: Callback sent BEFORE reply
print("\n✅ TEST 3: Callback Triggered (Before Reply)")
print("-"*80)
session2 = "test-002"
count = receive_scammer_message(session2)
print(f"Step 1: Received scammer message with intel → Count: {count}")
assert count == 1, f"Expected 1, got {count}"

print(f"Step 2: Intelligence extracted → Trigger callback")
callback_count = message_counts[session2]
print(f"Step 3: Callback sent with totalMessagesExchanged: {callback_count}")
assert callback_count == 1, f"Expected 1 (no reply sent yet), got {callback_count}"

print("Step 4: Return 410 Gone (no reply sent)")
print("✓ PASSED - Callback before reply: 1 message total (scammer only)")

# Test Scenario 4: Multiple exchanges then callback
print("\n✅ TEST 4: Multiple Exchanges Then Callback (Timeout)")
print("-"*80)
session3 = "test-003"
for i in range(3):
    count = receive_scammer_message(session3)
    print(f"Exchange {i+1}: Received scammer message → Count: {count}")
    count = send_agent_reply(session3)
    print(f"Exchange {i+1}: Sent agent reply → Count: {count}")

print(f"\nStep: Timeout reached")
callback_count = message_counts[session3]
print(f"Step: Callback sent with totalMessagesExchanged: {callback_count}")
assert callback_count == 6, f"Expected 6 (3 scammer + 3 agent), got {callback_count}"
print("✓ PASSED - After 3 exchanges + timeout: 6 messages total")

print("\n" + "="*80)
print("🎉 ALL MESSAGE COUNTING TESTS PASSED!")
print("\nKey Points:")
print("  ✅ +1 when scammer message received")
print("  ✅ +1 when agent reply actually sent")
print("  ✅ Callback uses count at time of trigger")
print("  ✅ If callback before reply: count = scammer messages only")
print("="*80)
