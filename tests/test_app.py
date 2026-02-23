"""
Integration tests for the Mergington High School API.

Tests cover all endpoints with comprehensive coverage including:
- Happy paths (successful requests)
- Error cases (404, 400 errors)
- Edge cases (max participants, duplicate signups)
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint (GET /)"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        
        # Verify expected activity names
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Swimming Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club"
        }
        assert set(activities.keys()) == expected_activities

    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            # Verify required fields
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            
            # Verify data types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            
            # Verify descriptions and schedules are not empty
            assert len(activity_data["description"]) > 0
            assert len(activity_data["schedule"]) > 0
            
            # Verify max_participants is positive
            assert activity_data["max_participants"] > 0

    def test_activities_have_participants_list(self, client):
        """Test that activities with existing participants are returned correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]
        
        # Programming Class should have 2 participants
        assert len(activities["Programming Class"]["participants"]) == 2
        
        # Gym Class should have 2 participants
        assert len(activities["Gym Class"]["participants"]) == 2
        
        # Basketball Team should start empty
        assert len(activities["Basketball Team"]["participants"]) == 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successful signup to an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "new_student@mergington.edu"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Signed up new_student@mergington.edu for Basketball Team"
        
        # Verify participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "new_student@mergington.edu" in activities["Basketball Team"]["participants"]

    def test_signup_multiple_students_to_same_activity(self, client):
        """Test multiple students can sign up to the same activity"""
        # First signup
        response1 = client.post(
            "/activities/Swimming Club/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second signup
        response2 = client.post(
            "/activities/Swimming Club/signup",
            params={"email": "student2@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are in participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities["Swimming Club"]["participants"]) == 2
        assert "student1@mergington.edu" in activities["Swimming Club"]["participants"]
        assert "student2@mergington.edu" in activities["Swimming Club"]["participants"]

    def test_duplicate_signup_rejected(self, client):
        """Test that duplicate signup for same activity is rejected"""
        email = "duplicate_student@mergington.edu"
        
        # First signup - should succeed
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email - should fail
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up"

    def test_signup_to_nonexistent_activity(self, client):
        """Test that signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_with_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        # Lowercase version should fail
        response = client.post(
            "/activities/basketball team/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_signup_to_full_activity(self, client):
        """Test signup behavior when activity reaches max participants"""
        # Chess Club has max_participants=12 and starts with 2
        # Add students until we reach the limit
        
        activity_name = "Chess Club"
        for i in range(10):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"chess_student{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Verify we have 12 participants (2 original + 10 added)
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities[activity_name]["participants"]) == 12
        
        # NOTE: Current app.py doesn't validate max_participants on signup
        # This test documents current behavior (allows overflow)
        # Future enhancement could enforce the max_participants limit
        response_overflow = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow_student@mergington.edu"}
        )
        # Currently succeeds, but could be changed to return 400 if needed
        assert response_overflow.status_code == 200

    def test_signup_response_format(self, client):
        """Test that signup response has correct format"""
        response = client.post(
            "/activities/Drama Club/signup",
            params={"email": "drama_student@mergington.edu"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "drama_student@mergington.edu" in data["message"]
        assert "Drama Club" in data["message"]


class TestActivityIntegration:
    """Integration tests across multiple endpoints"""

    def test_signup_and_retrieve_activity(self, client):
        """Test that signup updates are reflected in GET /activities"""
        email = "integration_test@mergington.edu"
        activity_name = "Science Club"
        
        # Initial check
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify in list
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in final_response.json()[activity_name]["participants"]

    def test_signup_same_student_different_activities(self, client):
        """Test that same student can signup for multiple different activities"""
        student_email = "active_student@mergington.edu"
        
        # Signup for multiple activities
        response1 = client.post(
            "/activities/Debate Team/signup",
            params={"email": student_email}
        )
        response2 = client.post(
            "/activities/Drama Club/signup",
            params={"email": student_email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert student_email in activities["Debate Team"]["participants"]
        assert student_email in activities["Drama Club"]["participants"]
