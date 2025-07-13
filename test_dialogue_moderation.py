#!/usr/bin/env python3
"""
Test script to validate the dialogue moderation flow end-to-end.
This simulates the complete workflow from event creation to dialogue moderation.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, endpoint, data=None, headers=None):
    """Make a request to the API"""
    url = f"{BASE_URL}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=default_headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"{method} {endpoint} -> {response.status_code}")
        if response.status_code >= 400:
            print(f"Error: {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_dialogue_moderation_flow():
    """Test the complete dialogue moderation flow"""
    print("🧪 Testing Dialogue Moderation Flow")
    print("=" * 50)
    
    # Step 1: Create admin session
    print("\n1️⃣ Creating admin session...")
    session_data = make_request("POST", "/auth/session/create", {
        "display_name": "Test Admin"
    })
    if not session_data:
        print("❌ Failed to create session")
        return False
    
    session_code = session_data.get("session_code")
    headers = {"X-Session-Code": session_code}
    print(f"✅ Session created: {session_code}")
    
    # Step 2: Create test event
    print("\n2️⃣ Creating test event...")
    event_data = make_request("POST", "/events/", {
        "title": "Test Dialogue Moderation",
        "description": "Testing the dialogue moderation workflow",
        "event_type": "discussion",
        "is_public": True,
        "allow_anonymous": False,
        "inquiries": [
            {
                "title": "Community Priority",
                "content": "What should be our community's top priority?",
                "inquiry_type": "open_ended",
                "required": True,
                "order_index": 0
            }
        ],
        "session_code": session_code
    }, headers)
    
    if not event_data:
        print("❌ Failed to create event")
        return False
    
    event_id = event_data.get("id")
    print(f"✅ Event created: {event_id}")
    
    # Step 3: Publish event
    print("\n3️⃣ Publishing event...")
    publish_result = make_request("POST", f"/events/{event_id}/publish", headers=headers)
    if not publish_result:
        print("❌ Failed to publish event")
        return False
    print("✅ Event published")
    
    # Step 4: Submit test responses
    print("\n4️⃣ Submitting test responses...")
    responses = [
        "I think affordable housing should be our top priority. Too many families are struggling with rent.",
        "Public transportation needs improvement. Better buses and bike lanes would help everyone.",
        "Education funding is critical. Our schools need more resources and smaller class sizes.",
        "Environmental protection matters most. We need to address climate change locally.",
        "Healthcare access is essential. We need more community health centers."
    ]
    
    for i, response_text in enumerate(responses):
        response_data = make_request("POST", "/responses/batch", [{
            "event_id": event_id,
            "round_number": 1,
            "inquiry_id": event_data["inquiries"][0]["id"],
            "content": response_text,
            "participant_code": f"participant_{i+1}"
        }], headers)
        if response_data:
            print(f"✅ Response {i+1} submitted")
        else:
            print(f"❌ Failed to submit response {i+1}")
    
    # Step 5: Check round state
    print("\n5️⃣ Checking round state...")
    round_state = make_request("GET", f"/events/{event_id}/round-state")
    if round_state:
        print(f"✅ Round state: {round_state.get('status')} (Round {round_state.get('current_round')})")
    
    # Step 6: Advance round (trigger analysis)
    print("\n6️⃣ Advancing round to trigger analysis...")
    advance_result = make_request("POST", f"/events/{event_id}/advance-round", headers=headers)
    if not advance_result:
        print("❌ Failed to advance round")
        return False
    print("✅ Round advanced - Analysis should be running...")
    
    # Step 7: Wait for analysis to complete and check round state
    print("\n7️⃣ Waiting for analysis to complete...")
    for attempt in range(10):  # Wait up to 10 attempts
        time.sleep(3)
        round_state = make_request("GET", f"/events/{event_id}/round-state")
        if round_state:
            status = round_state.get("status")
            round_num = round_state.get("current_round")
            print(f"   Attempt {attempt + 1}: Status = {status}, Round = {round_num}")
            
            if status == "admin_review":
                print("✅ Round transitioned to admin_review!")
                break
        else:
            print(f"   Attempt {attempt + 1}: Failed to get round state")
    else:
        print("❌ Round did not transition to admin_review within timeout")
        return False
    
    # Step 8: Test synthesis review endpoint
    print("\n8️⃣ Testing synthesis review endpoint...")
    synthesis_review = make_request("GET", f"/ai/synthesis-review/{event_id}/{round_num}", headers=headers)
    if synthesis_review:
        print("✅ Synthesis review data retrieved successfully!")
        print(f"   Summary: {synthesis_review.get('summary', 'N/A')[:100]}...")
        prompts = synthesis_review.get('next_round_prompts', [])
        print(f"   Generated {len(prompts)} prompts for next round")
        
        # Step 9: Test synthesis update
        print("\n9️⃣ Testing synthesis update...")
        synthesis_id = synthesis_review.get('id')
        if synthesis_id and prompts:
            # Modify first prompt
            prompts[0]['content'] = "EDITED: " + prompts[0]['content']
            update_result = make_request("PUT", f"/ai/synthesis-review/{synthesis_id}", {
                "next_round_prompts": prompts
            }, headers)
            if update_result:
                print("✅ Synthesis updated successfully!")
            else:
                print("❌ Failed to update synthesis")
        
        # Step 10: Test synthesis approval
        print("\n🔟 Testing synthesis approval...")
        if synthesis_id:
            approval_result = make_request("POST", f"/ai/synthesis-review/{synthesis_id}/approve", headers=headers)
            if approval_result:
                print("✅ Synthesis approved successfully!")
                print("✅ Dialogue moderation flow test PASSED!")
                return True
            else:
                print("❌ Failed to approve synthesis")
    else:
        print("❌ Failed to retrieve synthesis review data")
    
    return False

if __name__ == "__main__":
    success = test_dialogue_moderation_flow()
    sys.exit(0 if success else 1)