"""
Unit tests for background data-testid attribute validation.

This test ensures that the background element has the proper data-testid
attribute for E2E testing compatibility.
"""

import pytest
from bs4 import BeautifulSoup


def test_background_data_testid_presence():
    """Test that the background element has data-testid='background' attribute."""
    # Load the HTML file
    with open('apps/h-bridge/static/index.html', 'r') as f:
        html_content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find background element
    background = soup.find('div', {'data-testid': 'background'})
    
    # Assert background element exists
    assert background is not None, "Background element with data-testid='background' not found"
    
    # Verify it's the correct element (has id layer-bg)
    assert background.get('id') == 'layer-bg', "Background element should have id='layer-bg'"
    assert 'layer' in background.get('class', []), "Background element should have 'layer' class"


def test_background_element_structure():
    """Test that background element maintains expected structure."""
    with open('apps/h-bridge/static/index.html', 'r') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find background element by data-testid
    background = soup.find('div', {'data-testid': 'background'})
    
    # Check element structure
    assert background.name == 'div', "Background should be a div element"
    assert background.get('id') == 'layer-bg', "Background should maintain id='layer-bg'"
    assert background.get('class') == ['layer'], "Background should have 'layer' class"
    assert background.get('data-testid') == 'background', "Background should have data-testid='background'"


def test_no_duplicate_background_data_testids():
    """Test that there's only one element with data-testid='background'."""
    with open('apps/h-bridge/static/index.html', 'r') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements with data-testid='background'
    backgrounds = soup.find_all('div', {'data-testid': 'background'})
    
    # Should be exactly one
    assert len(backgrounds) == 1, f"Expected exactly 1 background element, found {len(backgrounds)}"


if __name__ == '__main__':
    test_background_data-testid_presence()
    test_background_element_structure()
    test_no_duplicate_background_data_testids()
    print("✅ All background data-testid tests passed!")