"""Test all 5 root cause scenarios for intermittent INVALID_REQUEST_BODY"""

from app.models import HoneypotRequest, Message

print('Testing all 5 root cause scenarios...')
print('='*60)

# Test 1: conversationHistory null
print('Test 1: conversationHistory null')
try:
    req = HoneypotRequest.model_validate({
        'sessionId': 'test-1',
        'message': {'sender': 'scammer', 'text': 'test', 'timestamp': 1738408530000},
        'conversationHistory': None
    })
    print(f'✅ PASS - conversationHistory: {req.conversationHistory}')
except Exception as e:
    print(f'❌ FAIL - {e}')

# Test 2: conversationHistory omitted
print('\nTest 2: conversationHistory omitted')
try:
    req = HoneypotRequest.model_validate({
        'sessionId': 'test-2',
        'message': {'sender': 'scammer', 'text': 'test', 'timestamp': 1738408530000}
    })
    print(f'✅ PASS - conversationHistory: {req.conversationHistory}')
except Exception as e:
    print(f'❌ FAIL - {e}')

# Test 3: sender variations
print('\nTest 3: sender variations (case-insensitive + trimming)')
for sender in ['Scammer', 'scammer ', ' USER', 'user', 'SCAMMER', '  scammer  ']:
    try:
        msg = Message(sender=sender, text='test', timestamp=1738408530000)
        print(f'✅ PASS - "{sender}" → "{msg.sender}"')
    except Exception as e:
        print(f'❌ FAIL - "{sender}" → {e}')

# Test 4: timestamp variations
print('\nTest 4: timestamp variations')
test_timestamps = [
    (1738408530000, 'int (Unix ms)'),
    ('1738408530000', 'string number'),
    ('2026-01-21T10:15:30Z', 'ISO-8601 with Z'),
    ('2026-01-21T10:15:30+00:00', 'ISO-8601 with +00:00')
]
for ts, desc in test_timestamps:
    try:
        msg = Message(sender='scammer', text='test', timestamp=ts)
        print(f'✅ PASS - {desc}: {ts}')
    except Exception as e:
        print(f'❌ FAIL - {desc}: {ts} → {e}')

# Test 5: timestamp null (should fail gracefully)
print('\nTest 5: timestamp null (expected to fail)')
try:
    msg = Message(sender='scammer', text='test', timestamp=None)
    print(f'⚠️  UNEXPECTED - None accepted (should fail)')
except Exception as e:
    print(f'✅ EXPECTED FAIL - {type(e).__name__}')

# Test 6: metadata variations
print('\nTest 6: metadata variations')
metadata_tests = [
    ({}, 'empty dict'),
    (None, 'null'),
    ({'channel': 'SMS'}, 'partial fields'),
    ({'channel': 'SMS', 'language': 'EN'}, 'some fields'),
    ({'channel': 'SMS', 'language': 'EN', 'locale': 'IN'}, 'all fields')
]
for meta, desc in metadata_tests:
    try:
        req = HoneypotRequest.model_validate({
            'sessionId': 'test-6',
            'message': {'sender': 'scammer', 'text': 'test', 'timestamp': 1738408530000},
            'metadata': meta
        })
        print(f'✅ PASS - {desc}: {meta}')
    except Exception as e:
        print(f'❌ FAIL - {desc}: {meta} → {e}')

print('='*60)
print('Summary: All 5 root causes should be handled')
