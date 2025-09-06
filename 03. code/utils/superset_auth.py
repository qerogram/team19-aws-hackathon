"""
Superset Authentication Manager
Handles authentication state and session management for Superset API
"""

import requests
import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

class SupersetAuthManager:
    """Singleton class to manage Superset authentication state"""
    _instance = None
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.csrf_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.base_url: str = os.getenv("SUPERSET_URL", "http://localhost:8088")
        self.username: str = os.getenv("SUPERSET_USERNAME", "")
        self.password: str = os.getenv("SUPERSET_PASSWORD", "")
        self.session = requests.Session()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance - useful for clearing stale authentication"""
        logging.info("[SUPERSET AUTH] Resetting singleton instance")
        cls._instance = None
        return cls.get_instance()
    
    def is_authenticated(self) -> bool:
        """Check if current authentication is valid"""
        if not self.access_token:
            return False
        if self.token_expiry and datetime.now() >= self.token_expiry:
            return False
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication tokens"""
        headers = {
            "Content-Type": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token
        return headers
    
    def authenticate(self) -> Dict[str, str]:
        """Authenticate with Superset and obtain tokens"""
        try:
            # Step 1: Login to get access token
            login_url = f"{self.base_url}/api/v1/security/login"
            login_payload = {
                "username": self.username,
                "password": self.password,
                "provider": "db",
                "refresh": True
            }
            
            logging.info(f"[SUPERSET AUTH] Attempting login to {login_url}")
            login_response = self.session.post(
                login_url,
                json=login_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code != 200:
                error_msg = f"Login failed with status {login_response.status_code}: {login_response.text}"
                logging.error(f"[SUPERSET AUTH] {error_msg}")
                return {"status": "error", "message": error_msg}
            
            login_data = login_response.json()
            self.access_token = login_data.get("access_token")
            self.refresh_token = login_data.get("refresh_token")
            
            # Set token expiry to 10 minutes for more frequent re-authentication
            self.token_expiry = datetime.now() + timedelta(minutes=10)
            
            logging.info(f"[SUPERSET AUTH] Successfully obtained access token")
            
            # Step 2: Get CSRF token
            csrf_url = f"{self.base_url}/api/v1/security/csrf_token/"
            csrf_response = self.session.get(
                csrf_url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                self.csrf_token = csrf_data.get("result")
                logging.info(f"[SUPERSET AUTH] Successfully obtained CSRF token")
            else:
                logging.warning(f"[SUPERSET AUTH] Could not obtain CSRF token: {csrf_response.status_code}")
            
            return {
                "status": "success",
                "message": "Successfully authenticated with Superset",
                "access_token": self.access_token[:20] + "..." if self.access_token else None,
                "csrf_token": self.csrf_token[:20] + "..." if self.csrf_token else None,
                "expires_at": self.token_expiry.isoformat() if self.token_expiry else None
            }
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Could not connect to Superset at {self.base_url}. Please ensure Superset is running."
            logging.error(f"[SUPERSET AUTH] {error_msg}")
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logging.error(f"[SUPERSET AUTH] {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def refresh_authentication(self) -> Dict[str, str]:
        """Refresh authentication tokens if needed"""
        if self.is_authenticated():
            return {
                "status": "success",
                "message": "Authentication still valid",
                "expires_at": self.token_expiry.isoformat() if self.token_expiry else None
            }
        return self.authenticate()
    
    def force_reauthenticate(self) -> Dict[str, str]:
        """Force reauthentication regardless of current token status"""
        logging.info("[SUPERSET AUTH] Force reauthentication requested")
        # Clear existing tokens
        self.access_token = None
        self.csrf_token = None
        self.refresh_token = None
        self.token_expiry = None
        # Create new session to avoid stale cookies
        self.session = requests.Session()
        # Authenticate
        return self.authenticate()
    
    def test_connection(self) -> Dict[str, any]:
        """Test the connection to Superset"""
        # Ensure we're authenticated
        if not self.is_authenticated():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": auth_result["message"]}
        
        try:
            # Test by getting database list
            test_url = f"{self.base_url}/api/v1/database/"
            response = self.session.get(
                test_url,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "database_count": data.get("count", 0),
                    "base_url": self.base_url
                }
            else:
                return {
                    "status": "error",
                    "message": f"Connection test failed with status {response.status_code}",
                    "details": response.text[:200]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test error: {str(e)}"
            }
    
    def get_database_id(self, database_name: str) -> Optional[int]:
        """Get database ID from database name"""
        # Ensure we're authenticated
        if not self.is_authenticated():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                logging.error(f"[SUPERSET AUTH] Failed to authenticate for database ID lookup")
                return None
        
        try:
            # Get database list
            db_list_url = f"{self.base_url}/api/v1/database/"
            response = self.session.get(
                db_list_url,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                databases = data.get("result", [])
                
                # Find matching database by name
                for db in databases:
                    if db.get("database_name") == database_name:
                        db_id = db.get("id")
                        logging.info(f"[SUPERSET AUTH] Found database '{database_name}' with ID: {db_id}")
                        return db_id
                
                # If not found, try to get first available database as fallback
                if databases:
                    fallback_db = databases[0]
                    logging.warning(f"[SUPERSET AUTH] Database '{database_name}' not found, using fallback: {fallback_db.get('database_name')} (ID: {fallback_db.get('id')})")
                    return fallback_db.get("id")
                
                logging.error(f"[SUPERSET AUTH] No databases found in Superset")
                return None
            else:
                logging.error(f"[SUPERSET AUTH] Failed to get database list: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"[SUPERSET AUTH] Error getting database ID: {str(e)}")
            return None
    
    def execute_query(self, sql: str, database_id: int = None, database_name: str = "PostgreSQL", query_limit: int = None) -> Dict[str, any]:
        """Execute SQL query via Superset SQL Lab API with flexible query limit control.
        
        Args:
            sql: SQL query to execute
            database_id: Database ID (optional, will lookup by name if not provided)
            database_name: Database name for lookup (default: simple_shop)
            query_limit: Maximum rows to return (default: 100, was 1000)
        """
        import uuid
        import time
        
        # Ensure we're authenticated
        if not self.is_authenticated():
            auth_result = self.authenticate()
            if auth_result["status"] != "success":
                return {"status": "error", "message": auth_result["message"]}
        
        # Get database ID if not provided
        if database_id is None:
            database_id = self.get_database_id(database_name)
            if database_id is None:
                return {"status": "error", "message": f"Could not find database: {database_name}"}
        
        # Set default query limit if not provided (reduced from 1000 to 100)
        if query_limit is None:
            query_limit = 100
            
        try:
            # Generate unique client ID (11 characters)
            client_id = str(uuid.uuid4())[:11]
            
            # Prepare SQL Lab execute request
            execute_url = f"{self.base_url}/api/v1/sqllab/execute/"
            payload = {
                "client_id": client_id,
                "database_id": database_id,
                "json": True,
                "runAsync": False,  # Run synchronously for simpler implementation
                "sql": sql,
                "sql_editor_id": str(uuid.uuid4())[:8],
                "tab": "Query",
                "tmp_table_name": "",
                "select_as_cta": False,
                "ctas_method": "TABLE",
                "queryLimit": query_limit,
                "expand_data": True
            }
            
            logging.info(f"[SUPERSET QUERY] Executing query on database ID {database_id}: {sql[:100]}...")
            
            # Execute query
            response = self.session.post(
                execute_url,
                json=payload,
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 202]:
                result_data = response.json()
                
                # Check if query is still running (async mode)
                if response.status_code == 202 or result_data.get("status") == "pending":
                    query_id = result_data.get("id") or result_data.get("query", {}).get("id")
                    logging.info(f"[SUPERSET QUERY] Query submitted, polling for results (ID: {query_id})")
                    
                    # Poll for results
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        time.sleep(1)
                        
                        # Check query status
                        status_url = f"{self.base_url}/api/v1/sqllab/results/?key={query_id}"
                        status_response = self.session.get(
                            status_url,
                            headers=self.get_headers()
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            query_status = status_data.get("status")
                            
                            if query_status == "success":
                                logging.info(f"[SUPERSET QUERY] Query completed successfully")
                                return {
                                    "status": "success",
                                    "data": status_data.get("data", []),
                                    "columns": status_data.get("columns", []),
                                    "query": status_data.get("query", {})
                                }
                            elif query_status == "error":
                                error_msg = status_data.get("error") or status_data.get("errors", ["Unknown error"])[0]
                                logging.error(f"[SUPERSET QUERY] Query failed: {error_msg}")
                                return {"status": "error", "message": f"Query error: {error_msg}"}
                    
                    return {"status": "error", "message": "Query timeout - took too long to execute"}
                
                # Query completed synchronously
                if result_data.get("status") == "success" or "data" in result_data:
                    logging.info(f"[SUPERSET QUERY] Query completed successfully")
                    return {
                        "status": "success",
                        "data": result_data.get("data", []),
                        "columns": result_data.get("columns", []),
                        "query": result_data.get("query", {})
                    }
                elif result_data.get("status") == "error":
                    error_msg = result_data.get("error") or result_data.get("errors", ["Unknown error"])[0]
                    logging.error(f"[SUPERSET QUERY] Query failed: {error_msg}")
                    return {"status": "error", "message": f"Query error: {error_msg}"}
                else:
                    # Unexpected response format
                    logging.warning(f"[SUPERSET QUERY] Unexpected response format: {result_data}")
                    return {
                        "status": "success",
                        "data": result_data.get("data", []),
                        "columns": result_data.get("columns", []),
                        "query": result_data
                    }
                    
            elif response.status_code == 401:
                # Handle 401 unauthorized - try to reauthenticate once
                logging.warning("[SUPERSET QUERY] Got 401 unauthorized, attempting reauthentication...")
                reauth_result = self.force_reauthenticate()
                if reauth_result["status"] == "success":
                    logging.info("[SUPERSET QUERY] Reauthentication successful, retrying query...")
                    # Retry the query with new authentication
                    retry_response = self.session.post(
                        execute_url,
                        json=payload,
                        headers=self.get_headers()
                    )
                    if retry_response.status_code in [200, 202]:
                        result_data = retry_response.json()
                        if result_data.get("status") == "success" or "data" in result_data:
                            logging.info(f"[SUPERSET QUERY] Query completed successfully after reauthentication")
                            return {
                                "status": "success",
                                "data": result_data.get("data", []),
                                "columns": result_data.get("columns", []),
                                "query": result_data.get("query", {})
                            }
                    error_text = retry_response.text[:500]
                    logging.error(f"[SUPERSET QUERY] Query failed after reauthentication: {error_text}")
                    return {"status": "error", "message": f"Query failed after reauthentication: {error_text}"}
                else:
                    return {"status": "error", "message": f"Reauthentication failed: {reauth_result['message']}"}
            else:
                error_text = response.text[:500]
                logging.error(f"[SUPERSET QUERY] Query execution failed with status {response.status_code}: {error_text}")
                return {"status": "error", "message": f"Query execution failed: {error_text}"}
                
        except Exception as e:
            logging.error(f"[SUPERSET QUERY] Exception during query execution: {str(e)}")
            return {"status": "error", "message": f"Query execution error: {str(e)}"}