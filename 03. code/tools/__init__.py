"""
Tools package for Data Agent
Organized by functionality: query, schema, auth, chart, dashboard
"""

from .query import execute_sql_query, explore_table_structure, execute_aggregation_query
from .schema import get_database_schema, list_available_tables
from .auth import authenticate_superset, get_superset_auth_status, test_superset_connection
from .chart import (
    create_superset_chart, 
    get_available_datasets, 
    get_chart_types,
    create_chart_from_query,
    list_existing_charts
)

def get_all_tools():
    """Return all available tools for the agent"""
    return [
        # Database query tools
        execute_sql_query,
        explore_table_structure,
        execute_aggregation_query,
        # Database schema tools
        get_database_schema,
        list_available_tables,
        # Superset authentication tools
        authenticate_superset,
        get_superset_auth_status,
        test_superset_connection,
        # Superset visualization tools
        create_superset_chart,
        get_available_datasets,
        get_chart_types,
        create_chart_from_query,
        list_existing_charts,
    ]

# For backward compatibility
get_tools = get_all_tools

__all__ = [
    'execute_sql_query',
    'explore_table_structure', 
    'execute_aggregation_query',
    'get_database_schema',
    'list_available_tables',
    'authenticate_superset',
    'get_superset_auth_status',
    'test_superset_connection',
    'create_superset_chart',
    'get_available_datasets',
    'get_chart_types',
    'create_chart_from_query',
    'list_existing_charts',
    'get_all_tools',
    'get_tools'
]