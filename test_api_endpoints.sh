#!/bin/bash
# Test script for Hunyuan 3D API endpoints

API_URL="http://localhost:8081"
AUTH="admin:admin"

echo "======================================"
echo "HUNYUAN 3D API ENDPOINT TEST"
echo "======================================"
echo

# Test 1: Health check
echo "📊 Test 1: Health Check"
curl -s "$API_URL/health" | jq
echo

# Test 2: Metrics
echo "📈 Test 2: Metrics Endpoint"
curl -s "$API_URL/metrics" | head -10
echo "..."
echo

# Test 3: OpenAPI spec
echo "📋 Test 3: Available Endpoints"
curl -s "$API_URL/openapi.json" | jq -r '.paths | keys[]'
echo

# Test 4: Generate (async with minimal image)
echo "🎨 Test 4: Generate 3D Mesh (Async)"
echo "Sending generation request..."

# Create minimal test image (1x1 red pixel)
TEST_IMAGE_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

# Send request
RESPONSE=$(curl -s -X POST "$API_URL/generate" \
  -u "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{
    \"image\": \"$TEST_IMAGE_B64\",
    \"num_inference_steps\": 5,
    \"guidance_scale\": 1.0,
    \"seed\": 42,
    \"model\": \"Normal\"
  }")

echo "Response: $RESPONSE"

# Check if we got a uid (async) or error
if echo "$RESPONSE" | jq -e '.uid' > /dev/null 2>&1; then
    UID=$(echo "$RESPONSE" | jq -r '.uid')
    echo "✅ Generation started! UID: $UID"
    echo
    
    # Test 5: Check status
    echo "⏳ Test 5: Checking Status (polling every 5s)..."
    for i in {1..20}; do
        sleep 5
        STATUS=$(curl -s "$API_URL/status/$UID")
        STATE=$(echo "$STATUS" | jq -r '.state' 2>/dev/null || echo "error")
        echo "  [$i] State: $STATE"
        
        if [ "$STATE" == "completed" ]; then
            echo "✅ Generation completed!"
            echo "$STATUS" | jq
            break
        elif [ "$STATE" == "error" ] || [ "$STATE" == "null" ]; then
            echo "❌ Generation failed or invalid response"
            echo "$STATUS"
            break
        fi
    done
else
    echo "❌ Generation failed to start"
    echo "$RESPONSE" | jq 2>/dev/null || echo "$RESPONSE"
fi

echo
echo "======================================"
echo "TEST COMPLETE"
echo "======================================"
