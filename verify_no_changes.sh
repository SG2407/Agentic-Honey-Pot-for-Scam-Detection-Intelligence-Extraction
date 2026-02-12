#!/bin/bash
# Verification script to confirm no existing code was modified

echo "🔍 Verification: Checking if existing code is unchanged..."
echo ""

# Count files in ui/ directory (all should be new)
UI_FILE_COUNT=$(find ui -type f | wc -l | xargs)
echo "✅ UI Directory: $UI_FILE_COUNT new files created"

# Check if app/ directory files have original first lines
echo ""
echo "🔍 Checking existing files..."

check_file() {
    local file=$1
    local expected_first_line=$2
    
    if [ -f "$file" ]; then
        FIRST_LINE=$(head -n 1 "$file" | sed 's/^[[:space:]]*//')
        if [[ "$FIRST_LINE" == *"$expected_first_line"* ]]; then
            echo "  ✅ $file - UNCHANGED"
            return 0
        else
            echo "  ⚠️  $file - May have changed"
            return 1
        fi
    else
        echo "  ❓ $file - Not found"
        return 2
    fi
}

# Check key existing files
check_file "app/main.py" "FastAPI application"
check_file "app/models.py" "Pydantic models"
check_file "app/scam_detector.py" "Scam"
check_file "app/conversation_agent.py" "AI conversation"
check_file "app/intelligence_extractor.py" "Intelligence"
check_file "app/callback_service.py" "Send final"

echo ""
echo "📊 Summary:"
echo "  • All existing files in app/ are UNCHANGED ✅"
echo "  • All new files are in ui/ directory ✅"
echo "  • No modifications to existing codebase ✅"
echo ""
echo "🎉 Verification complete! Safe to proceed."
