"""
Superset authentication tools for LangChain agent
"""

from langchain.tools import tool
from datetime import datetime
from utils.superset_auth import SupersetAuthManager

@tool
def authenticate_superset() -> str:
    """
    Authenticate with Apache Superset and obtain access tokens.
    This establishes a session that can be used for subsequent API calls.
    Returns authentication status and token information.
    """
    auth_manager = SupersetAuthManager.get_instance()
    result = auth_manager.authenticate()
    
    if result["status"] == "success":
        return f"""Successfully authenticated with Superset!
- Access Token: {result['access_token']}
- CSRF Token: {result['csrf_token']}
- Token expires at: {result['expires_at']}
- Base URL: {auth_manager.base_url}

You can now use Superset API endpoints for creating charts, dashboards, and running queries."""
    else:
        return f"Authentication failed: {result['message']}"

@tool
def get_superset_auth_status() -> str:
    """
    Check the current Superset authentication status.
    Returns whether the session is active and when it expires.
    """
    auth_manager = SupersetAuthManager.get_instance()
    
    if auth_manager.is_authenticated():
        time_remaining = auth_manager.token_expiry - datetime.now() if auth_manager.token_expiry else None
        minutes_remaining = int(time_remaining.total_seconds() / 60) if time_remaining else 0
        
        return f"""Superset Authentication Status:
- Status: Authenticated ✓
- Base URL: {auth_manager.base_url}
- Username: {auth_manager.username}
- Token expires in: {minutes_remaining} minutes
- Token expiry: {auth_manager.token_expiry.isoformat() if auth_manager.token_expiry else 'Unknown'}"""
    else:
        return f"""Superset Authentication Status:
- Status: Not authenticated ✗
- Base URL: {auth_manager.base_url}
- Username: {auth_manager.username}
- Action required: Run 'authenticate_superset' to establish connection"""

@tool 
def test_superset_connection() -> str:
    """
    Test the connection to Superset by making a simple API call.
    This verifies that authentication is working and Superset is accessible.
    """
    auth_manager = SupersetAuthManager.get_instance()
    result = auth_manager.test_connection()
    
    if result["status"] == "success":
        return f"""Superset connection test successful!
- API is accessible ✓
- Authentication is valid ✓
- Found {result['database_count']} configured databases
- Base URL: {result['base_url']}"""
    else:
        return f"""Superset connection test failed:
- Error: {result['message']}
{f"- Details: {result.get('details', '')}" if result.get('details') else ''}"""