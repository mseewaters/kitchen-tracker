# Create: backend/src/kitchen_tracker/utils/timezone_utils.py

from datetime import date, datetime, timedelta
import pytz

# Set your timezone - change this to your actual timezone
HOUSEHOLD_TIMEZONE = pytz.timezone('America/New_York')  # EDT/EST

def get_local_date() -> date:
    """Get today's date in the household timezone"""
    utc_now = datetime.now(pytz.UTC)
    local_now = utc_now.astimezone(HOUSEHOLD_TIMEZONE)
    return local_now.date()

def get_local_datetime() -> datetime:
    """Get current datetime in the household timezone"""
    utc_now = datetime.now(pytz.UTC)
    return utc_now.astimezone(HOUSEHOLD_TIMEZONE)

def get_local_date_string() -> str:
    """Get today's date as ISO string in household timezone"""
    return get_local_date().isoformat()

def get_local_datetime_string() -> str:
    """Get current datetime as ISO string in household timezone"""
    return get_local_datetime().isoformat()

def get_date_days_ago(days: int) -> str:
    """Get date N days ago in household timezone as ISO string"""
    local_date = get_local_date()
    past_date = local_date - timedelta(days=days)
    return past_date.isoformat()

# Replace all instances of:
# - date.today() → get_local_date()
# - date.today().isoformat() → get_local_date_string()
# - datetime.utcnow().isoformat() → get_local_datetime_string()