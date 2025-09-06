"""
Superset Chart and Visualization Tools for LangChain Agent
"""

from langchain.tools import tool
from typing import Dict, List, Optional
import json
import logging
from utils.superset_auth import SupersetAuthManager

@tool
def create_superset_chart(
    datasource_id: int = 1,
    chart_type: str = "table",
    chart_name: str = None,
    metric: str = "count",
    dimensions: List[str] = None,
    filters: List[Dict] = None
) -> str:
    """
    Create a new chart in Superset.
    
    Args:
        datasource_id: ID of the dataset/table to use
        chart_type: Type of chart (e.g., 'table', 'bar', 'line', 'pie', 'big_number', 'scatter')
        chart_name: Name for the chart (optional)
        metric: Metric to display (e.g., 'count', 'sum', 'avg')
        dimensions: List of dimension columns for grouping
        filters: List of filter conditions
    
    Returns:
        Chart creation result with URL and chart ID
    """
    auth_manager = SupersetAuthManager.get_instance()
    
    if not auth_manager.is_authenticated():
        return "Error: Not authenticated with Superset. Please run authenticate_superset first."
    
    # Generate chart name if not provided
    if not chart_name:
        import datetime
        chart_name = f"Chart_{chart_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Map chart types to Superset viz types
    viz_type_mapping = {
        "table": "table",
        "bar": "echarts_timeseries_bar",
        "line": "echarts_timeseries_line",
        "pie": "pie",
        "area": "echarts_area",
        "scatter": "echarts_scatter",
        "heatmap": "heatmap",
        "boxplot": "box_plot",
        "big_number": "big_number_total"
    }
    
    viz_type = viz_type_mapping.get(chart_type.lower(), "table")
    
    # Prepare filters
    adhoc_filters = []
    if filters:
        for f in filters:
            adhoc_filters.append({
                "clause": "WHERE",
                "subject": f.get("column", ""),
                "operator": f.get("operator", "="),
                "comparator": f.get("value", ""),
                "expressionType": "SIMPLE"
            })
    else:
        # Default no filter
        adhoc_filters = [{
            "clause": "WHERE",
            "subject": "created_at",
            "operator": "TEMPORAL_RANGE",
            "comparator": "No filter",
            "expressionType": "SIMPLE"
        }]
    
    # Prepare params based on viz type
    params = {
        "datasource": f"{datasource_id}__table",
        "viz_type": viz_type,
        "adhoc_filters": adhoc_filters,
        "extra_form_data": {},
        "dashboards": []
    }
    
    # Add viz-specific parameters
    if viz_type == "big_number_total":
        params.update({
            "metric": metric,
            "header_font_size": 0.4,
            "subtitle_font_size": 0.15,
            "metric_name_font_size": 0.15,
            "y_axis_format": "SMART_NUMBER",
            "time_format": "smart_date"
        })
    elif viz_type == "table":
        params.update({
            "metrics": [metric],
            "columns": dimensions or [],
            "row_limit": 10000
        })
    elif viz_type in ["echarts_timeseries_bar", "echarts_timeseries_line", "echarts_area"]:
        params.update({
            "metrics": [metric],
            "groupby": dimensions or [],
            "row_limit": 10000
        })
    elif viz_type == "pie":
        params.update({
            "metric": metric,
            "groupby": dimensions or [],
            "row_limit": 10
        })
    else:
        params.update({
            "metrics": [metric],
            "row_limit": 10000
        })
    
    # Prepare query context
    query_context = {
        "datasource": {"id": datasource_id, "type": "table"},
        "force": False,
        "queries": [{
            "filters": [{"col": f["column"], "op": f.get("operator", "="), "val": f["value"]} for f in (filters or [])],
            "extras": {"having": "", "where": ""},
            "applied_time_extras": {},
            "columns": dimensions or [],
            "metrics": [metric],
            "annotation_layers": [],
            "series_limit": 0,
            "group_others_when_limit_reached": False,
            "order_desc": True,
            "url_params": {},
            "custom_params": {},
            "custom_form_data": {}
        }],
        "form_data": params,
        "result_format": "json",
        "result_type": "full"
    }
    
    # Prepare the request body
    chart_config = {
        "params": json.dumps(params),
        "slice_name": chart_name,
        "viz_type": viz_type,
        "datasource_id": datasource_id,
        "datasource_type": "table",
        "dashboards": [],
        "owners": [],
        "query_context": json.dumps(query_context)
    }
    
    try:
        import requests
        response = requests.post(
            f"{auth_manager.base_url}/api/v1/chart/",
            json=chart_config,
            headers=auth_manager.get_headers()
        )
        
        if response.status_code == 201:
            response_data = response.json()
            
            # Handle both response formats
            if "result" in response_data:
                chart_data = response_data["result"]
                chart_id = response_data.get("id", chart_data.get("id"))
            else:
                chart_data = response_data
                chart_id = chart_data.get("id")
            
            chart_url = f"{auth_manager.base_url}/explore/?slice_id={chart_id}"
            
            return f"""Chart created successfully!
- Chart Name: {chart_name}
- Chart Type: {chart_type}
- Chart ID: {chart_id}
- View URL: {chart_url}
- Edit URL: {auth_manager.base_url}/chart/edit/{chart_id}"""
        else:
            return f"Failed to create chart: {response.status_code} - {response.text}"
            
    except Exception as e:
        logging.error(f"Error creating chart: {str(e)}")
        return f"Error creating chart: {str(e)}"

@tool
def get_available_datasets() -> str:
    """
    Get list of available datasets in Superset that can be used for visualization.
    
    Returns:
        List of available datasets with their IDs and names
    """
    auth_manager = SupersetAuthManager.get_instance()
    
    if not auth_manager.is_authenticated():
        return "Error: Not authenticated with Superset. Please run authenticate_superset first."
    
    try:
        import requests
        response = requests.get(
            f"{auth_manager.base_url}/api/v1/dataset/",
            headers=auth_manager.get_headers(),
            params={"page_size": 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            datasets = data.get("result", [])
            
            if not datasets:
                return "No datasets found in Superset."
            
            result = "Available Datasets:\n"
            for ds in datasets:
                result += f"- ID: {ds['id']}, Name: {ds['table_name']}, Database: {ds.get('database', {}).get('database_name', 'Unknown')}\n"
            
            return result
        else:
            return f"Failed to fetch datasets: {response.status_code} - {response.text}"
            
    except Exception as e:
        logging.error(f"Error fetching datasets: {str(e)}")
        return f"Error fetching datasets: {str(e)}"

@tool
def get_chart_types() -> str:
    """
    Get list of available chart types that can be created in Superset.
    
    Returns:
        List of supported chart types with descriptions
    """
    chart_types = [
        {"type": "table", "description": "Basic table view of data"},
        {"type": "bar", "description": "Bar chart for categorical comparisons"},
        {"type": "line", "description": "Line chart for trends over time"},
        {"type": "pie", "description": "Pie chart for proportional data"},
        {"type": "area", "description": "Area chart for cumulative trends"},
        {"type": "scatter", "description": "Scatter plot for correlation analysis"},
        {"type": "heatmap", "description": "Heatmap for matrix data visualization"},
        {"type": "boxplot", "description": "Box plot for statistical distributions"}
    ]
    
    result = "Available Chart Types:\n"
    for chart in chart_types:
        result += f"- {chart['type']}: {chart['description']}\n"
    
    result += "\nUsage Tips:\n"
    result += "- Use 'bar' for comparing categories\n"
    result += "- Use 'line' for time series data\n"
    result += "- Use 'pie' for showing parts of a whole\n"
    result += "- Use 'scatter' for finding correlations\n"
    result += "- Use 'table' for detailed data inspection\n"
    
    return result

@tool
def create_chart_from_query(
    query: str,
    chart_type: str = "auto",
    chart_name: str = None,
    database_id: int = 1
) -> str:
    """
    Execute a SQL query and create a chart from the results.
    Note: This is a simplified approach. For complex charts, use create_superset_chart directly.
    
    Args:
        query: SQL query to execute
        chart_type: Type of chart or 'auto' for automatic selection
        chart_name: Name for the chart (optional)
        database_id: Database ID to run the query against
    
    Returns:
        Query results and chart creation status
    """
    auth_manager = SupersetAuthManager.get_instance()
    
    if not auth_manager.is_authenticated():
        return "Error: Not authenticated with Superset. Please run authenticate_superset first."
    
    # Auto-detect chart type based on query pattern if set to 'auto'
    if chart_type == "auto":
        query_lower = query.lower()
        if "count(*)" in query_lower and "group by" not in query_lower:
            chart_type = "big_number"
        elif "group by" in query_lower and "count" in query_lower:
            chart_type = "bar"
        elif "date" in query_lower or "time" in query_lower:
            chart_type = "line"
        elif "sum" in query_lower and "group by" in query_lower:
            chart_type = "pie"
        else:
            chart_type = "table"
        
        logging.info(f"Auto-selected chart type: {chart_type}")
    
    # Parse query to extract metrics and dimensions (simplified)
    query_lower = query.lower()
    metric = "count"  # Default metric
    dimensions = []
    
    # Try to extract metric
    if "count(*)" in query_lower or "count(" in query_lower:
        metric = "count"
    elif "sum(" in query_lower:
        metric = "sum"
    elif "avg(" in query_lower:
        metric = "avg"
    elif "max(" in query_lower:
        metric = "max"
    elif "min(" in query_lower:
        metric = "min"
    
    # Try to extract dimensions from GROUP BY
    if "group by" in query_lower:
        group_by_part = query_lower.split("group by")[1].split("order by")[0].split("having")[0]
        dimensions = [dim.strip() for dim in group_by_part.split(",") if dim.strip()]
    
    # First execute the query to validate it
    try:
        import requests
        
        # Execute query via Superset SQL Lab API
        sql_payload = {
            "database_id": database_id,
            "sql": query,
            "runAsync": False,
            "schema": None
        }
        
        response = requests.post(
            f"{auth_manager.base_url}/api/v1/sqllab/execute/",
            json=sql_payload,
            headers=auth_manager.get_headers()
        )
        
        if response.status_code != 200:
            return f"Query execution failed: {response.status_code} - {response.text}"
        
        query_result = response.json()
        row_count = len(query_result.get("data", []))
        
        # Create visualization using the new format
        chart_result = create_superset_chart(
            datasource_id=database_id,
            chart_type=chart_type,
            chart_name=chart_name,
            metric=metric,
            dimensions=dimensions
        )
        
        return f"""Query executed and visualization created!

Query Statistics:
- Rows returned: {row_count}
- Selected chart type: {chart_type}
- Metric: {metric}
- Dimensions: {', '.join(dimensions) if dimensions else 'None'}

{chart_result}"""
        
    except Exception as e:
        logging.error(f"Error in create_chart_from_query: {str(e)}")
        return f"Error: {str(e)}"

@tool 
def list_existing_charts(page_size: int = 20) -> str:
    """
    List existing charts in Superset.
    
    Args:
        page_size: Number of charts to return (default 20)
    
    Returns:
        List of existing charts with their details
    """
    auth_manager = SupersetAuthManager.get_instance()
    
    if not auth_manager.is_authenticated():
        return "Error: Not authenticated with Superset. Please run authenticate_superset first."
    
    try:
        import requests
        response = requests.get(
            f"{auth_manager.base_url}/api/v1/chart/",
            headers=auth_manager.get_headers(),
            params={"page_size": page_size}
        )
        
        if response.status_code == 200:
            data = response.json()
            charts = data.get("result", [])
            
            if not charts:
                return "No charts found in Superset."
            
            result = f"Existing Charts (showing {len(charts)} of {data.get('count', 0)}):\n\n"
            for chart in charts:
                result += f"- Name: {chart.get('slice_name', 'Unnamed')}\n"
                result += f"  ID: {chart.get('id')}\n"
                result += f"  Type: {chart.get('viz_type', 'Unknown')}\n"
                result += f"  URL: {auth_manager.base_url}/explore/?slice_id={chart.get('id')}\n"
                result += f"  Last Modified: {chart.get('changed_on_delta_humanized', 'Unknown')}\n\n"
            
            return result
        else:
            return f"Failed to fetch charts: {response.status_code} - {response.text}"
            
    except Exception as e:
        logging.error(f"Error fetching charts: {str(e)}")
        return f"Error fetching charts: {str(e)}"