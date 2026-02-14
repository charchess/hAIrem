"""
Simple integration test for Audio Ingestion functionality
Tests that audio components work together end-to-end
"""

import pytest
import requests
import time


def test_audio_endpoints_available():
    """Test that audio-related endpoints and components are accessible."""
    base_url = "http://localhost:8000"
    
    # Test that main page loads
    response = requests.get(base_url)
    assert response.status_code == 200
    assert "audio-toggle" in response.text
    
    # Test that audio.js is accessible
    js_response = requests.get(f"{base_url}/static/js/audio.js")
    assert js_response.status_code == 200
    assert "AudioCapture" in js_response.text
    
    # Test that main server is responding
    health_response = requests.get(f"{base_url}/api/agents")
    assert health_response.status_code in [200, 404]  # 404 is ok if endpoints not yet implemented
    
    print("✅ All audio components accessible")


def test_message_types_extended():
    """Test that HLink message types include audio support."""
    # Test import from project root
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'h-bridge', 'src'))
    
    try:
        from models.hlink import MessageType
        
        # Check for new audio message types
        assert hasattr(MessageType, 'USER_AUDIO')
        assert hasattr(MessageType, 'AUDIO_RECEIVED')
        assert hasattr(MessageType, 'AUDIO_ERROR')
        
        # Check values
        assert MessageType.USER_AUDIO == "user_audio"
        assert MessageType.AUDIO_RECEIVED == "audio_received"
        assert MessageType.AUDIO_ERROR == "audio_error"
        
        print("✅ Audio message types properly defined")
        
    except ImportError as e:
        pytest.fail(f"Could not import audio message types: {e}")


def test_audio_ui_components():
    """Test that audio UI components are present in HTML."""
    base_url = "http://localhost:8000"
    
    response = requests.get(base_url)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Check for audio control elements
    assert "id=\"audio-toggle\"" in html_content
    assert "id=\"audio-status\"" in html_content
    assert "audio-controls" in html_content
    
    # Check for audio.js script inclusion
    assert "audio.js" in html_content
    
    print("✅ Audio UI components present")


def test_server_functionality():
    """Test that server is running and functional."""
    base_url = "http://localhost:8000"
    
    try:
        # Test WebSocket endpoint exists
        response = requests.get(base_url)
        assert response.status_code == 200
        
        # Test static files are served
        js_response = requests.get(f"{base_url}/static/js/renderer.js")
        assert js_response.status_code == 200
        
        css_response = requests.get(f"{base_url}/static/style.css")
        assert css_response.status_code == 200
        
        print("✅ Server functionality verified")
        
    except requests.exceptions.ConnectionError:
        pytest.fail("Server is not running or not accessible")


if __name__ == "__main__":
    # Run all tests if executed directly
    test_audio_endpoints_available()
    test_message_types_extended()
    test_audio_ui_components()
    test_server_functionality()
    print("✅ All audio integration tests passed!")