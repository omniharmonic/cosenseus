#!/usr/bin/env python3
"""
Create a test event that will be ready for dialogue moderation interface testing.
"""

import requests
import json
import time

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

def create_moderation_ready_event():
    """Create an event ready for dialogue moderation"""
    print("🎭 Creating Event Ready for Dialogue Moderation")
    print("=" * 50)
    
    # Step 1: Create admin session
    print("\n1️⃣ Creating admin session...")
    session_data = make_request("POST", "/auth/session/create", {
        "display_name": "Admin User"
    })
    if not session_data:
        return None
    
    session_code = session_data.get("session_code")
    headers = {"X-Session-Code": session_code}
    print(f"✅ Session: {session_code}")
    
    # Step 2: Create event
    print("\n2️⃣ Creating event...")
    event_data = make_request("POST", "/events/", {
        "title": "UI Test: Community Planning Session", 
        "description": "A test event to demonstrate the dialogue moderation interface. Please review and edit the AI-generated prompts for Round 2.",
        "event_type": "discussion",
        "is_public": True,
        "allow_anonymous": False,
        "inquiries": [
            {
                "title": "Vision for Our Community",
                "content": "What is your vision for our community's future? What would make it an even better place to live, work, and thrive?",
                "inquiry_type": "open_ended",
                "required": True,
                "order_index": 0
            }
        ],
        "session_code": session_code
    }, headers)
    
    if not event_data:
        return None
    
    event_id = event_data.get("id")
    print(f"✅ Event: {event_id}")
    
    # Step 3: Publish event
    print("\n3️⃣ Publishing event...")
    publish_result = make_request("POST", f"/events/{event_id}/publish", headers=headers)
    if not publish_result:
        return None
    print("✅ Published")
    
    # Step 4: Submit diverse responses
    print("\n4️⃣ Submitting responses...")
    responses = [
        "I envision a community with more green spaces and parks where families can gather and children can play safely.",
        "We need better public transportation that connects all neighborhoods and reduces our carbon footprint.",
        "Affordable housing should be a priority - no one should have to choose between rent and other necessities.",
        "Local businesses need support through community events and farmers markets that bring people together.",
        "Education and youth programs are essential for giving our children opportunities to succeed.",
        "Community gardens would help with food security while bringing neighbors together.",
        "Better accessibility for seniors and people with disabilities is important for inclusivity.",
        "Arts and cultural programs would enrich our community spirit and celebrate our diversity."
    ]
    
    inquiry_id = event_data["inquiries"][0]["id"]
    for i, response_text in enumerate(responses):
        response_data = make_request("POST", "/responses/batch", [{
            "event_id": event_id,
            "round_number": 1,
            "inquiry_id": inquiry_id,
            "content": response_text,
            "participant_code": f"test_participant_{i+1}"
        }], headers)
        if response_data:
            print(f"✅ Response {i+1}")
        else:
            print(f"❌ Response {i+1} failed")
    
    # Step 5: Advance to analysis
    print("\n5️⃣ Advancing to analysis...")
    advance_result = make_request("POST", f"/events/{event_id}/advance-round", headers=headers)
    if not advance_result:
        return None
    print("✅ Analysis starting...")
    
    # Step 6: Wait for admin_review state
    print("\n6️⃣ Waiting for admin review state...")
    for attempt in range(15):
        time.sleep(2)
        round_state = make_request("GET", f"/events/{event_id}/round-state")
        if round_state:
            status = round_state.get("status")
            round_num = round_state.get("current_round")
            print(f"   Status: {status}, Round: {round_num}")
            
            if status == "admin_review":
                print(f"\n🎉 SUCCESS! Event ready for moderation testing:")
                print(f"   📋 Event ID: {event_id}")
                print(f"   🔗 Frontend URL: http://localhost:3000/events/{event_id}")
                print(f"   📝 Session Code: {session_code}")
                print(f"   🎭 Status: {status} (Round {round_num})")
                print(f"\n👆 Use the session code above to log in as admin and test the moderation interface!")
                return {
                    "event_id": event_id,
                    "session_code": session_code,
                    "round_number": round_num,
                    "status": status
                }
    
    print("❌ Timeout waiting for admin_review state")
    return None

if __name__ == "__main__":
    result = create_moderation_ready_event()
    if result:
        print(f"\n✅ Test event created successfully!")
    else:
        print(f"\n❌ Failed to create test event")