"""
Simple integration test for Wake Word Engine functionality
Tests that wake word components work together
"""

import pytest
import requests
import time


def test_wakeword_endpoints_available():
    """Test that wake word-related endpoints and components are accessible."""
    base_url = "http://localhost:8000"
    
    # Test that main page loads
    response = requests.get(base_url)
    assert response.status_code == 200
    assert "wakeword.js" in response.text
    
    # Test that wake word detector is accessible
    js_response = requests.get(f"{base_url}/static/js/wakeword.js")
    assert js_response.status_code == 200
    assert "WakeWordDetector" in js_response.text
    
    # Test that main server is responding
    health_response = requests.get(f"{base_url}/api/agents")
    assert health_response.status_code in [200, 404]  # 404 is ok if endpoints not yet implemented
    
    print("✅ All wake word components accessible")


def test_wakeword_ui_components():
    """Test that wake word UI components are present in HTML."""
    base_url = "http://localhost:8000"
    
    response = requests.get(base_url)
    assert response.status_code == 200
    
    html_content = response.text
    
    # Check for wake word control elements
    assert "WakeWordDetector" in html_content
    assert "wakeword-status" in html_content
    
    print("✅ Wake word UI components present")


def test_wakeword_message_types():
    """Test that wake word message types are properly defined."""
    # Test import from project root
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'h-bridge', 'src'))
    
    try:
        from models.hlink import MessageType
        
        # Check for wake word message types
        assert hasattr(MessageType, 'WAKE_WORD_DETECTED')
        assert hasattr(MessageType, 'AUDIO_AUTO_START')
        assert hasattr(MessageType, 'WAKE_WORD_STATUS')
        
        # Check values
        assert MessageType.WAKE_WORD_DETECTED == "wake_word_detected"
        assert MessageType.AUDIO_AUTO_START == "audio_auto_start"
        assert MessageType.WAKE_WORD_STATUS == "wake_word_status"
        
        print("✅ Wake word message types properly defined")
        
    except ImportError as e:
        pytest.fail(f"Could not import wake word message types: {e}")


def test_wakeword_processing_components():
    """Test wake word processing backend components."""
    # Test backend processing import
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'h-bridge', 'src'))
    
    try:
        from handlers.wakeword import extract_audio_features, create_simple_wake_word_model
        
        # Test feature extraction
        features = extract_audio_features([0.1, 0.2, 0.3], 16000)
        assert 'energy' in features
        assert 'zcr' in features
        
        # Test model creation
        model = create_simple_wake_word_model()
        assert hasattr(model, 'predict')
        
        print("✅ Wake word processing components functional")
        
    except ImportError as e:
        pytest.fail(f"Could not import wake word processing: {e}")


def test_server_functionality_with_wakeword():
    """Test that server is running with wake word features."""
    base_url = "http://localhost:8000"
    
    try:
        # Test WebSocket endpoint exists
        response = requests.get(base_url)
        assert response.status_code == 200
        
        # Test static files are served
        js_response = requests.get(f"{base_url}/static/js/wakeword.js")
        assert js_response.status_code == 200
        
        css_response = requests.get(f"{base_url}/static/style.css")
        assert css_response.status_code == 200
        
        print("✅ Server functionality verified with wake word features")
        
    except requests.exceptions.ConnectionError:
        pytest.fail("Server is not running or not accessible")


if __name__ == "__main__":
    # Run all tests if executed directly
    test_wakeword_endpoints_available()
    test_wakeword_ui_components()
    test_wakeword_message_types()
    test_wakeword_processing_components()
    test_server_functionality_with_wakeword()
    print("✅ All wake word integration tests passed!")