import pytest
from unittest.mock import patch
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'kitchen_tracker'))

# Import the functions we want to test
from app import parse_homechef_email, calculate_week_of

class TestEmailParser:
    """Unit tests for Home Chef email parsing functions"""
    
    def test_calculate_week_of_thursday_delivery(self):
        """Test week calculation for Thursday delivery"""
        # Thursday, July 3 should map to Monday of that week
        week_of = calculate_week_of("Thursday, July 3")
        
        # Should return Monday's date in YYYY-MM-DD format
        assert len(week_of) == 10  # YYYY-MM-DD format
        assert week_of.endswith("-06-30") or week_of.endswith("-07-01")  # Depending on year, could be June 30 or July 1
        
        # Parse the date and verify it's a Monday
        from datetime import datetime
        date_obj = datetime.strptime(week_of, "%Y-%m-%d")
        assert date_obj.weekday() == 0  # Monday is 0
    
    def test_calculate_week_of_friday_delivery(self):
        """Test week calculation for Friday delivery"""
        week_of = calculate_week_of("Friday, July 25")
        
        # Should be Monday of that week
        from datetime import datetime
        date_obj = datetime.strptime(week_of, "%Y-%m-%d")
        assert date_obj.weekday() == 0  # Monday
    
    def test_calculate_week_of_invalid_date(self):
        """Test week calculation with invalid date falls back gracefully"""
        week_of = calculate_week_of("Invalid Date String")
        
        # Should fallback to current week's Monday
        assert len(week_of) == 10  # YYYY-MM-DD format
        
        from datetime import datetime
        date_obj = datetime.strptime(week_of, "%Y-%m-%d")
        assert date_obj.weekday() == 0  # Monday
    
    def test_parse_homechef_email_with_real_structure(self):
        """Test parsing a Home Chef email with the actual structure"""
        # Sample HTML content based on the real Home Chef email structure
        sample_html_email = '''
        Content-Type: text/html; charset="utf-8"
        Content-Transfer-Encoding: base64
        
        PGh0bWw+DQo8aGVhZD4NCjx0aXRsZT5Zb3VyIEhvbWUgQ2hlZiBvcmRlciBpcyBvbiBpdHMgd2F5ITwvdGl0bGU+DQo8L2hlYWQ+DQo8Ym9keT4NCjxwPkhpIE1hcmpvcmllLDwvcD4NCjxwPllvdXIgSG9tZSBDaGVmIG9yZGVyIGlzIG9uIGl0cyB3YXkgYW5kIGlzIHNjaGVkdWxlZCB0byBhcnJpdmUgYnkgZW5kIG9mIHRoZSBkYXkgb24gPHN0cm9uZz5UaHVyc2RheSwgSnVseSAzPC9zdHJvbmc+LjwvcD4NCjxhIGhyZWY9Imh0dHBzOi8vY2xpY2suZS5ob21lY2hlZi5jb20vP3FzPXRlc3QxIiB0YXJnZXQ9Il9ibGFuayIgc3R5bGU9ImNvbG9yOiM0YTRhNGE7IGZvbnQtd2VpZ2h0OmJvbGQ7IHRleHQtZGVjb3JhdGlvbjpub25lIj5NYXJnaGVyaXRhIENoaWNrZW48L2E+DQo8YSBocmVmPSJodHRwczovL2NsaWNrLmUuaG9tZWNoZWYuY29tLz9xcz10ZXN0MiIgdGFyZ2V0PSJfYmxhbmsiIHN0eWxlPSJjb2xvcjojNGE0YTRhOyBmb250LXdlaWdodDpib2xkOyB0ZXh0LWRlY29yYXRpb246bm9uZSI+RGlqb24gYW5kIERpbGwgQ3JlYW0gVHJvdXQ8L2E+DQo8L2JvZHk+DQo8L2h0bWw+
        '''
        
        meals = parse_homechef_email(sample_html_email)
        
        assert len(meals) == 2
        assert meals[0]['name'] == 'Margherita Chicken'
        assert meals[0]['delivery_date'] == 'Thursday, July 3'
        assert meals[0]['recipe_link'] == 'https://click.e.homechef.com/?qs=test1'
        assert meals[0]['is_tracking_link'] is True
        
        assert meals[1]['name'] == 'Dijon and Dill Cream Trout'
        assert meals[1]['recipe_link'] == 'https://click.e.homechef.com/?qs=test2'
    
    def test_parse_homechef_email_no_html(self):
        """Test parsing email with no HTML content"""
        text_only_email = '''
        From: test@example.com
        To: user@example.com
        Subject: Test
        Content-Type: text/plain
        
        This is a plain text email with no HTML content.
        '''
        
        meals = parse_homechef_email(text_only_email)
        assert meals == []
    
    def test_parse_homechef_email_no_delivery_date(self):
        """Test parsing email without delivery date"""
        html_without_date = '''
        Content-Type: text/html; charset="utf-8"
        Content-Transfer-Encoding: base64
        
        PGh0bWw+DQo8Ym9keT4NCjxhIGhyZWY9Imh0dHBzOi8vY2xpY2suZS5ob21lY2hlZi5jb20vP3FzPXRlc3QiIHRhcmdldD0iX2JsYW5rIiBzdHlsZT0iY29sb3I6IzRhNGE0YTsgZm9udC13ZWlnaHQ6Ym9sZDsgdGV4dC1kZWNvcmF0aW9uOm5vbmUiPlRlc3QgTWVhbDwvYT4NCjwvYm9keT4NCjwvaHRtbD4=
        '''
        
        meals = parse_homechef_email(html_without_date)
        assert len(meals) == 1
        assert meals[0]['name'] == 'Test Meal'
        assert meals[0]['delivery_date'] is None
    
    def test_parse_homechef_email_filters_non_meal_links(self):
        """Test that non-meal links are filtered out"""
        html_with_nav_links = '''
        Content-Type: text/html; charset="utf-8"
        Content-Transfer-Encoding: base64
        
        PGh0bWw+DQo8Ym9keT4NCjxhIGhyZWY9Imh0dHBzOi8vY2xpY2suZS5ob21lY2hlZi5jb20vP3FzPW1lYWwiIHRhcmdldD0iX2JsYW5rIiBzdHlsZT0iY29sb3I6IzRhNGE0YTsgZm9udC13ZWlnaHQ6Ym9sZDsgdGV4dC1kZWNvcmF0aW9uOm5vbmUiPkFjdHVhbCBNZWFsIE5hbWU8L2E+DQo8YSBocmVmPSJodHRwczovL2NsaWNrLmUuaG9tZWNoZWYuY29tLz9xcz1tZW51IiB0YXJnZXQ9Il9ibGFuayIgc3R5bGU9ImNvbG9yOiM0YTRhNGE7IGZvbnQtd2VpZ2h0OmJvbGQ7IHRleHQtZGVjb3JhdGlvbjpub25lIj5NZW51PC9hPg0KPGEgaHJlZj0iaHR0cHM6Ly9jbGljay5lLmhvbWVjaGVmLmNvbS8/cXM9YWNjb3VudCIgdGFyZ2V0PSJfYmxhbmsiIHN0eWxlPSJjb2xvcjojNGE0YTRhOyBmb250LXdlaWdodDpib2xkOyB0ZXh0LWRlY29yYXRpb246bm9uZSI+QWNjb3VudDwvYT4NCjwvYm9keT4NCjwvaHRtbD4=
        '''
        
        meals = parse_homechef_email(html_with_nav_links)
        
        # Should only extract the actual meal, not Menu/Account links
        assert len(meals) == 1
        assert meals[0]['name'] == 'Actual Meal Name'
    
    def test_parse_homechef_email_handles_malformed_html(self):
        """Test parsing email with malformed HTML"""
        malformed_html = '''
        Content-Type: text/html; charset="utf-8"
        
        <html><body>
        <a href="https://test.com" style="color:#4a4a4a; font-weight:bold;">Incomplete Meal Name
        <p>Some other content</p>
        </body></html>
        '''
        
        # Should not crash and return empty results for malformed content
        meals = parse_homechef_email(malformed_html)
        assert isinstance(meals, list)
        # May or may not find meals depending on how malformed, but shouldn't crash