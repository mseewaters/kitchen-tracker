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
        # Create a properly structured multipart email
        sample_html_content = '''<html>
<head><title>Your Home Chef order is on its way!</title></head>
<body>
<p>Hi Marjorie,</p>
<p>Your Home Chef order is on its way and is scheduled to arrive by end of the day on <strong>Thursday, July 3</strong>.</p>
<a href="https://click.e.homechef.com/?qs=test1" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Margherita Chicken</a>
<a href="https://click.e.homechef.com/?qs=test2" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Dijon and Dill Cream Trout</a>
</body>
</html>'''
        
        sample_email = f'''From: noreply@homechef.com
To: user@example.com
Subject: Your Home Chef order is on its way!
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Plain text version here

--boundary123
Content-Type: text/html; charset="utf-8"

{sample_html_content}

--boundary123--'''
        
        meals = parse_homechef_email(sample_email)
        
        assert len(meals) == 2
        assert meals[0]['name'] == 'Margherita Chicken'
        assert meals[0]['delivery_date'] == 'Thursday, July 3'
        assert meals[0]['recipe_link'] == 'https://click.e.homechef.com/?qs=test1'
        assert meals[0]['is_tracking_link'] is True
        
        assert meals[1]['name'] == 'Dijon and Dill Cream Trout'
        assert meals[1]['recipe_link'] == 'https://click.e.homechef.com/?qs=test2'
    
    def test_parse_homechef_email_no_html(self):
        """Test parsing email with no HTML content"""
        text_only_email = '''From: test@example.com
To: user@example.com
Subject: Test
Content-Type: text/plain

This is a plain text email with no HTML content.'''
        
        meals = parse_homechef_email(text_only_email)
        assert meals == []
    
    def test_parse_homechef_email_no_delivery_date(self):
        """Test parsing email without delivery date"""
        html_content = '''<html><body>
<a href="https://click.e.homechef.com/?qs=test" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Test Meal</a>
</body></html>'''
        
        sample_email = f'''From: noreply@homechef.com
To: user@example.com
Subject: Test
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/html; charset="utf-8"

{html_content}

--boundary123--'''
        
        meals = parse_homechef_email(sample_email)
        assert len(meals) == 1
        assert meals[0]['name'] == 'Test Meal'
        assert meals[0]['delivery_date'] is None
    
    def test_parse_homechef_email_filters_non_meal_links(self):
        """Test that non-meal links are filtered out"""
        html_content = '''<html><body>
<a href="https://click.e.homechef.com/?qs=meal" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Actual Meal Name</a>
<a href="https://click.e.homechef.com/?qs=menu" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Menu</a>
<a href="https://click.e.homechef.com/?qs=account" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none">Account</a>
</body></html>'''
        
        sample_email = f'''From: noreply@homechef.com
To: user@example.com
Subject: Test
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/html; charset="utf-8"

{html_content}

--boundary123--'''
        
        meals = parse_homechef_email(sample_email)
        
        # Should only extract the actual meal, not Menu/Account links
        assert len(meals) == 1
        assert meals[0]['name'] == 'Actual Meal Name'
    
    def test_parse_homechef_email_handles_malformed_html(self):
        """Test parsing email with malformed HTML"""
        malformed_content = '''<html><body>
<a href="https://test.com" style="color:#4a4a4a; font-weight:bold;">Incomplete Meal Name
<p>Some other content</p>
</body></html>'''
        
        sample_email = f'''From: test@example.com
To: user@example.com
Subject: Test
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/html; charset="utf-8"

{malformed_content}

--boundary123--'''
        
        # Should not crash and return empty results for malformed content
        meals = parse_homechef_email(sample_email)
        assert isinstance(meals, list)
        # May or may not find meals depending on how malformed, but shouldn't crash