from langchain.tools import tool
import logging
import time
import re
from utils.superset_auth import SupersetAuthManager

@tool
def execute_sql_query(query: str, database: str = "PostgreSQL", limit: int = 100) -> str:
    """Execute general SQL queries with automatic LIMIT clause to prevent large result sets.
    
    Best for: Detailed data inspection when specific rows are needed.
    Default limit: 100 rows (use limit parameter to adjust).
    
    Args:
        query: SQL query to execute
        database: Database name to execute query against (default: PostgreSQL)
        limit: Maximum rows to return (default: 100, max recommended: 1000)
    
    Returns:
        Formatted query results or error message
    """
    start_time = time.time()
    
    # Check if query already has LIMIT clause
    query_upper = query.upper()
    if 'LIMIT' not in query_upper and limit:
        # Add LIMIT clause to prevent large result sets
        query = query.rstrip().rstrip(';') + f" LIMIT {limit}"
        logging.info(f"[SQL EXECUTE] Auto-added LIMIT {limit} to query")
    
    logging.info(f"[SQL EXECUTE] Starting SQL query via Superset API: {query[:100]}...")
    
    # Warn if requesting too many rows
    if limit and limit > 1000:
        logging.warning(f"[SQL EXECUTE] Large limit requested: {limit} rows. Consider using aggregation instead.")
    
    try:
        # Get SupersetAuthManager instance
        auth_manager = SupersetAuthManager.get_instance()
        
        # Execute query via Superset with specified limit
        result = auth_manager.execute_query(sql=query, database_name=database, query_limit=limit)
        
        if result["status"] == "error":
            return f"Error executing query: {result['message']}\nQuery: {query}"
        
        # Extract data and columns from result
        data = result.get("data", [])
        columns = result.get("columns", [])
        
        # Format results
        if not data:
            return f"Query executed successfully. No results found.\nQuery: {query}"
        
        # Extract column names
        if columns:
            column_names = [col.get("column_name", col.get("name", f"col_{i}")) for i, col in enumerate(columns)]
        elif data:
            # Fallback: use keys from first row if columns not provided
            column_names = list(data[0].keys()) if data else []
        else:
            column_names = []
        
        # Build formatted result string
        result_str = f"Query: {query}\n\n"
        
        if column_names:
            # Add column headers
            result_str += " | ".join(column_names) + "\n"
            result_str += "-" * (len(" | ".join(column_names))) + "\n"
            
            # Add data rows (limit to 10 for display)
            for row in data[:10]:
                if isinstance(row, dict):
                    # Row is a dictionary
                    row_values = []
                    for col in column_names:
                        val = row.get(col, "NULL")
                        row_values.append(str(val) if val is not None else "NULL")
                else:
                    # Row is a list/tuple
                    row_values = [str(val) if val is not None else "NULL" for val in row]
                
                result_str += " | ".join(row_values) + "\n"
            
            if len(data) > 10:
                result_str += f"\n... and {len(data) - 10} more rows"
        else:
            # Fallback formatting if no column info
            result_str += str(data[:10])
            if len(data) > 10:
                result_str += f"\n... and {len(data) - 10} more rows"
        
        result_str += f"\n\nTotal rows: {len(data)}"
        
        elapsed = time.time() - start_time
        logging.info(f"[SQL EXECUTE] Query completed successfully in {elapsed:.2f}s via Superset API")
        
        return result_str
        
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"[SQL EXECUTE] Error after {elapsed:.2f}s: {str(e)}")
        return f"Error executing query: {str(e)}\nQuery: {query}"

@tool
def explore_table_structure(table_name: str, database: str = "PostgreSQL") -> str:
    """Explore ACTUAL table structure from live database with real-time data.
    
    Provides technical schema information including:
    - Actual column names and data types from the database
    - Real sample data (5 rows) to verify data format
    - Live statistics (row count, etc.)
    
    Best for: Verifying actual database structure and inspecting real data.
    Use together with get_database_schema for complete understanding
    (this tool shows WHAT exists, get_database_schema explains WHAT it MEANS).
    
    Args:
        table_name: Name of the table to explore
        database: Database name (default: PostgreSQL)
    
    Returns:
        Live table structure with sample data and current statistics
    """
    start_time = time.time()
    logging.info(f"[TABLE EXPLORE] Exploring table structure for: {table_name}")
    
    try:
        auth_manager = SupersetAuthManager.get_instance()
        
        # Query 1: Get sample data (5 rows)
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_result = auth_manager.execute_query(
            sql=sample_query, 
            database_name=database, 
            query_limit=5
        )
        
        # Query 2: Get table statistics
        stats_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT *) as approx_unique_rows
        FROM {table_name}
        """
        
        # Try to get statistics, but don't fail if it doesn't work
        try:
            stats_result = auth_manager.execute_query(
                sql=stats_query,
                database_name=database,
                query_limit=10
            )
        except:
            # Fallback to simple count
            stats_query = f"SELECT COUNT(*) as total_rows FROM {table_name}"
            stats_result = auth_manager.execute_query(
                sql=stats_query,
                database_name=database,
                query_limit=10
            )
        
        # Format response
        result_str = f"=== Table Structure: {table_name} ===\n\n"
        
        # Add sample data
        if sample_result["status"] == "success":
            data = sample_result.get("data", [])
            columns = sample_result.get("columns", [])
            
            result_str += "**Sample Data (5 rows):**\n"
            
            if columns:
                column_names = [col.get("column_name", col.get("name", f"col_{i}")) 
                               for i, col in enumerate(columns)]
            elif data:
                column_names = list(data[0].keys()) if data else []
            else:
                column_names = []
            
            if column_names and data:
                # Column headers
                result_str += " | ".join(column_names) + "\n"
                result_str += "-" * (len(" | ".join(column_names))) + "\n"
                
                # Data rows
                for row in data:
                    if isinstance(row, dict):
                        row_values = []
                        for col in column_names:
                            val = row.get(col, "NULL")
                            row_values.append(str(val)[:50] if val is not None else "NULL")
                    else:
                        row_values = [str(val)[:50] if val is not None else "NULL" for val in row]
                    result_str += " | ".join(row_values) + "\n"
            else:
                result_str += "No data found or table is empty.\n"
        else:
            result_str += f"Error getting sample data: {sample_result.get('message', 'Unknown error')}\n"
        
        # Add statistics
        result_str += "\n**Table Statistics:**\n"
        if stats_result["status"] == "success":
            stats_data = stats_result.get("data", [])
            if stats_data:
                for key, value in stats_data[0].items():
                    result_str += f"- {key}: {value}\n"
        else:
            result_str += "Could not retrieve statistics\n"
        
        # Add column info
        result_str += f"\n**Columns Found:** {len(column_names) if 'column_names' in locals() else 0}\n"
        if 'column_names' in locals() and column_names:
            result_str += f"Column Names: {', '.join(column_names)}\n"
        
        elapsed = time.time() - start_time
        logging.info(f"[TABLE EXPLORE] Exploration completed in {elapsed:.2f}s")
        
        return result_str
        
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"[TABLE EXPLORE] Error after {elapsed:.2f}s: {str(e)}")
        return f"Error exploring table: {str(e)}\nTable: {table_name}"

@tool
def execute_aggregation_query(query: str, database: str = "PostgreSQL") -> str:
    """Execute aggregation queries optimized for analytical operations.
    
    Best for: GROUP BY, COUNT, SUM, AVG, MIN, MAX operations.
    Optimized for queries that return summarized/aggregated results.
    
    Args:
        query: SQL aggregation query to execute
        database: Database name (default: PostgreSQL)
    
    Returns:
        Aggregated query results
    """
    start_time = time.time()
    
    # Validate it looks like an aggregation query
    query_upper = query.upper()
    aggregation_keywords = ['GROUP BY', 'COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 
                           'HAVING', 'DISTINCT', 'AGGREGATE']
    
    is_aggregation = any(keyword in query_upper for keyword in aggregation_keywords)
    
    if not is_aggregation:
        logging.warning(f"[AGG QUERY] Query doesn't appear to be an aggregation. Consider using execute_sql_query instead.")
    
    logging.info(f"[AGG QUERY] Starting aggregation query: {query[:100]}...")
    
    try:
        auth_manager = SupersetAuthManager.get_instance()
        
        # Execute with lower limit since aggregations typically return fewer rows
        result = auth_manager.execute_query(
            sql=query, 
            database_name=database,
            query_limit=100  # Aggregations rarely need more than 100 rows
        )
        
        if result["status"] == "error":
            return f"Error executing aggregation query: {result['message']}\nQuery: {query}"
        
        # Extract and format results
        data = result.get("data", [])
        columns = result.get("columns", [])
        
        if not data:
            return f"Aggregation query executed successfully. No results found.\nQuery: {query}"
        
        # Extract column names
        if columns:
            column_names = [col.get("column_name", col.get("name", f"col_{i}")) 
                           for i, col in enumerate(columns)]
        elif data:
            column_names = list(data[0].keys()) if data else []
        else:
            column_names = []
        
        # Build formatted result
        result_str = f"=== Aggregation Results ===\n"
        result_str += f"Query: {query}\n\n"
        
        if column_names:
            # Add headers
            result_str += " | ".join(column_names) + "\n"
            result_str += "-" * (len(" | ".join(column_names))) + "\n"
            
            # Add all rows (aggregations typically have fewer rows)
            for row in data:
                if isinstance(row, dict):
                    row_values = []
                    for col in column_names:
                        val = row.get(col, "NULL")
                        row_values.append(str(val) if val is not None else "NULL")
                else:
                    row_values = [str(val) if val is not None else "NULL" for val in row]
                result_str += " | ".join(row_values) + "\n"
        else:
            result_str += str(data)
        
        result_str += f"\n**Total result rows:** {len(data)}"
        
        elapsed = time.time() - start_time
        logging.info(f"[AGG QUERY] Aggregation completed in {elapsed:.2f}s")
        
        return result_str
        
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"[AGG QUERY] Error after {elapsed:.2f}s: {str(e)}")
        return f"Error executing aggregation query: {str(e)}\nQuery: {query}"