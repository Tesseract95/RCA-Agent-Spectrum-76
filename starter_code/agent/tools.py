"""
LangGraph tools for the Network Investigation Agent.
Each tool provides access to specific database queries.
"""
from typing import Any, Optional
from langchain_core.tools import tool
import json

from ..db_duckdb import (
    get_anomaly_by_id,
    get_all_anomalies,
    get_device_by_hostname,
    get_devices_by_hostnames,
    get_telemetry_for_device,
    get_syslogs_for_device,
    search_syslogs_by_keyword,
    run_query,
)


@tool
def get_anomaly_details(anomaly_id: str) -> str:
    """
    Retrieve detailed information about a specific network anomaly by its ID.
    
    Use this tool when the user provides an anomaly_id or when you need to investigate
    a specific detected anomaly. The returned information includes severity, detection
    window, impacted devices, and detector-specific details.
    
    Args:
        anomaly_id: The UUID of the anomaly (e.g., 'a1f0c8e2-1b44-4d90-9c31-000000000001')
    
    Returns:
        JSON string containing anomaly details including model_output with detector info,
        impacted hostnames, severity, and time window
    """
    result = get_anomaly_by_id(anomaly_id)
    
    if not result:
        return json.dumps({
            "error": f"No anomaly found with ID: {anomaly_id}",
            "suggestion": "Use list_all_anomalies to see available anomaly IDs"
        })
    
    return json.dumps(result, indent=2, default=str)


@tool
def list_all_anomalies() -> str:
    """
    List all detected anomalies in the system, ordered by date (most recent first).
    
    Use this tool to:
    - Get an overview of all detected anomalies
    - Find anomaly IDs for investigation
    - Answer questions about the number or types of anomalies
    
    Returns:
        JSON string containing list of all anomalies with basic info
    """
    results = get_all_anomalies()
    
    # Create a simplified view for listing
    simplified = []
    for anomaly in results:
        model_output = anomaly.get('model_output', {})
        
        # Parse JSON if it's a string
        if isinstance(model_output, str):
            model_output = json.loads(model_output)
        
        simplified.append({
            "anomaly_id": anomaly['anomaly_id'],
            "date": str(anomaly['anomaly_date']),
            "severity": anomaly['severity'],
            "detector": model_output.get('detector', 'unknown'),
            "impacted_hosts": model_output.get('impacted_hostnames', []),
            "host_count": model_output.get('host_count', 0)
        })
    
    return json.dumps(simplified, indent=2)


@tool
def get_device_information(hostname: str) -> str:
    """
    Retrieve detailed information about a network device by its hostname.
    
    Use this tool to:
    - Get device type, role, and location information
    - Find device_id for telemetry queries
    - Understand device topology and connections (from notes field)
    - Check WAN circuit information for SD-WAN devices
    
    Args:
        hostname: The hostname of the device (case-sensitive, e.g., 'FAIRVIEW-EDG01')
    
    Returns:
        JSON string containing device inventory details, location, and topology notes
    """
    result = get_device_by_hostname(hostname)
    
    if not result:
        return json.dumps({
            "error": f"No device found with hostname: {hostname}",
            "suggestion": "Check the hostname spelling - it is case-sensitive"
        })
    
    return json.dumps(result, indent=2, default=str)


@tool
def get_multiple_devices_info(hostnames: str) -> str:
    """
    Retrieve information about multiple network devices at once.
    
    Use this tool when an anomaly impacts multiple devices and you need to get
    their details together.
    
    Args:
        hostnames: Comma-separated list of hostnames (e.g., 'FAIRVIEW-EDG01,stonebridge-edg01')
    
    Returns:
        JSON string containing device information for all requested hostnames
    """
    hostname_list = [h.strip() for h in hostnames.split(',')]
    results = get_devices_by_hostnames(hostname_list)
    
    if not results:
        return json.dumps({
            "error": "No devices found with the provided hostnames",
            "provided": hostname_list
        })
    
    return json.dumps(results, indent=2, default=str)


@tool
def query_device_telemetry(
    device_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Query telemetry metrics for a specific device within a time range.
    
    Use this tool to:
    - Analyze device performance metrics (CPU, memory, temperature)
    - Check interface status (interfaces_up_ratio, error counts, flap counts)
    - Review BGP peer counts for routers
    - Check SD-WAN path quality metrics (latency, jitter, packet loss)
    - Investigate firewall session counts and policy denies
    
    Args:
        device_id: The device_id from network_devices table
        start_time: Start time in ISO format (e.g., '2026-07-08 06:00:00'), optional
        end_time: End time in ISO format (e.g., '2026-07-08 08:00:00'), optional
        limit: Maximum number of records to return (default 50)
    
    Returns:
        JSON string containing telemetry records with timestamp and metrics
    """
    results = get_telemetry_for_device(device_id, start_time, end_time, limit)
    
    if not results:
        return json.dumps({
            "message": f"No telemetry data found for device_id: {device_id}",
            "params": {
                "device_id": device_id,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit
            }
        })
    
    return json.dumps(results, indent=2, default=str)


@tool
def query_device_syslogs(
    device_id: Optional[str] = None,
    hostname: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    severity: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Query system logs for a device within a time range and with optional filters.
    
    Use this tool to:
    - Find specific log events during an anomaly window
    - Check for interface flaps, BGP session changes, policy denies
    - Search for change references (e.g., CHG-2026-0611)
    - Review error and critical messages
    - Correlate logs with anomalies
    
    Args:
        device_id: The device_id (optional, provide either device_id or hostname)
        hostname: The hostname (optional, provide either device_id or hostname)
        start_time: Start time in ISO format, optional
        end_time: End time in ISO format, optional
        severity: Filter by severity ('info', 'warning', 'error', 'critical'), optional
        message_type: Filter by type ('interface', 'routing', 'bgp', 'vpn', 'policy', etc.), optional
        limit: Maximum number of records to return (default 50)
    
    Returns:
        JSON string containing syslog entries with timestamps and messages
    """
    results = get_syslogs_for_device(
        device_id=device_id,
        hostname=hostname,
        start_time=start_time,
        end_time=end_time,
        severity=severity,
        message_type=message_type,
        limit=limit
    )
    
    if not results:
        return json.dumps({
            "message": "No syslog entries found matching the criteria",
            "params": {
                "device_id": device_id,
                "hostname": hostname,
                "start_time": start_time,
                "end_time": end_time,
                "severity": severity,
                "message_type": message_type,
                "limit": limit
            }
        })
    
    return json.dumps(results, indent=2, default=str)


@tool
def search_logs_by_keyword(
    keyword: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 30
) -> str:
    """
    Search system logs across all devices for a specific keyword or phrase.
    
    Use this tool to:
    - Find logs mentioning specific interfaces (e.g., 'xe-0/0/21')
    - Search for change ticket references (e.g., 'CHG-2026')
    - Find error messages or specific events
    - Cross-reference devices mentioned in logs
    
    Args:
        keyword: The keyword or phrase to search for in log messages
        start_time: Start time in ISO format, optional
        end_time: End time in ISO format, optional
        limit: Maximum number of records to return (default 30)
    
    Returns:
        JSON string containing matching syslog entries
    """
    results = search_syslogs_by_keyword(keyword, start_time, end_time, limit)
    
    if not results:
        return json.dumps({
            "message": f"No logs found containing keyword: {keyword}",
            "params": {
                "keyword": keyword,
                "start_time": start_time,
                "end_time": end_time
            }
        })
    
    return json.dumps(results, indent=2, default=str)


@tool
def execute_custom_query(sql_query: str) -> str:
    """
    Execute a custom SQL query against the DuckDB database.
    
    Use this tool for complex queries that aren't covered by other tools, such as:
    - Aggregations and statistics
    - Complex joins across tables
    - Custom time-based analysis
    
    IMPORTANT: Only use SELECT queries. Do not use INSERT, UPDATE, DELETE, or DDL statements.
    
    Available tables:
    - detected_anomalies (anomaly_id, severity, model_output, anomaly_date)
    - network_devices (device_id, hostname, device_type, role, site_code, notes, etc.)
    - device_telemetry (device_id, timestamp, cpu_utilization_pct, memory_utilization_pct, etc.)
    - device_syslogs (device_id, hostname, timestamp, severity, message_type, message)
    
    Args:
        sql_query: A SELECT SQL query string
    
    Returns:
        JSON string containing query results
    """
    # Safety check - only allow SELECT queries
    query_upper = sql_query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return json.dumps({
            "error": "Only SELECT queries are allowed",
            "provided_query": sql_query
        })
    
    # Additional safety checks
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return json.dumps({
                "error": f"Query contains forbidden keyword: {keyword}",
                "provided_query": sql_query
            })
    
    try:
        results = run_query(sql_query)
        return json.dumps({
            "query": sql_query,
            "row_count": len(results),
            "results": results
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({
            "error": f"Query execution failed: {str(e)}",
            "query": sql_query
        })


# Export all tools as a list
ALL_TOOLS = [
    get_anomaly_details,
    list_all_anomalies,
    get_device_information,
    get_multiple_devices_info,
    query_device_telemetry,
    query_device_syslogs,
    search_logs_by_keyword,
    execute_custom_query,
]
