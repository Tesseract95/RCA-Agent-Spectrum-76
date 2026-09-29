"""
DuckDB adapter for the Network Investigation Agent.
Loads CSV data into DuckDB for fast querying.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any
from contextlib import contextmanager

import duckdb
import pandas as pd
from dotenv import load_dotenv

# Load .env from parent directory (project root) or current directory
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Try current directory

# Path to the database file
DB_PATH = os.environ.get("DUCKDB_PATH", "network_rca.duckdb")
SEED_DATA_PATH = Path(__file__).parent.parent / "db" / "seed"


class DuckDBManager:
    """Singleton manager for DuckDB connections"""
    
    _instance = None
    _db_path = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._db_path = DB_PATH
            self._ensure_database_initialized()
            self._initialized = True
    
    def _ensure_database_initialized(self):
        """Initialize database with CSV data if tables don't exist"""
        # Use a temporary connection to check and initialize
        conn = duckdb.connect(self._db_path)
        
        try:
            # Check if tables already exist
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            
            if "detected_anomalies" in table_names:
                # Database already initialized
                print(f"DuckDB database already initialized at {self._db_path}")
                return
            
            print("Initializing DuckDB from CSV files...")
            
            # Load detected_anomalies - keep model_output as string, don't parse to dict
            anomalies_df = pd.read_csv(SEED_DATA_PATH / "detected_anomalies.csv")
            # model_output is already a valid JSON string in the CSV, keep it as-is
            conn.execute("CREATE TABLE detected_anomalies AS SELECT * FROM anomalies_df")
            
            # Load network_devices
            devices_df = pd.read_csv(SEED_DATA_PATH / "network_devices.csv")
            conn.execute("CREATE TABLE network_devices AS SELECT * FROM devices_df")
            
            # Load device_telemetry
            telemetry_df = pd.read_csv(SEED_DATA_PATH / "device_telemetry.csv")
            # Parse timestamp
            telemetry_df['timestamp'] = pd.to_datetime(telemetry_df['timestamp'])
            conn.execute("CREATE TABLE device_telemetry AS SELECT * FROM telemetry_df")
            
            # Load device_syslogs
            syslogs_df = pd.read_csv(SEED_DATA_PATH / "device_syslogs.csv")
            syslogs_df['timestamp'] = pd.to_datetime(syslogs_df['timestamp'])
            conn.execute("CREATE TABLE device_syslogs AS SELECT * FROM syslogs_df")
            
            print("Database initialized successfully!")
            print(f"  - detected_anomalies: {len(anomalies_df)} rows")
            print(f"  - network_devices: {len(devices_df)} rows")
            print(f"  - device_telemetry: {len(telemetry_df)} rows")
            print(f"  - device_syslogs: {len(syslogs_df)} rows")
        finally:
            conn.close()
    
    def get_connection(self):
        """Get a new read-only connection for each query"""
        # Return a fresh connection each time to avoid locking issues
        return duckdb.connect(self._db_path, read_only=True)


# Global instance
_db_manager = DuckDBManager()


@contextmanager
def get_connection():
    """Context manager for getting a DuckDB connection"""
    conn = _db_manager.get_connection()
    try:
        yield conn
    finally:
        conn.close()  # Always close the connection after use


def run_query(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    """
    Executes a SQL query and returns a list of plain dicts.
    
    Args:
        sql: SQL query string (use $param for named parameters)
        params: Dictionary of parameters for named parameter queries
    
    Returns:
        List of dictionaries representing rows
    
    Example:
        run_query("SELECT * FROM detected_anomalies WHERE anomaly_id = $id", {"id": anomaly_id})
    """
    with get_connection() as conn:
        if params:
            result = conn.execute(sql, params).fetchall()
        else:
            result = conn.execute(sql).fetchall()
        
        # Get column names
        if result:
            columns = [desc[0] for desc in conn.description]
            rows = []
            for row in result:
                row_dict = dict(zip(columns, row))
                
                # Parse model_output if it's a string (DuckDB JSON handling)
                if 'model_output' in row_dict and isinstance(row_dict['model_output'], str):
                    try:
                        row_dict['model_output'] = json.loads(row_dict['model_output'])
                    except:
                        pass  # Keep as string if parsing fails
                
                rows.append(row_dict)
            return rows
        return []


def list_tables() -> list[str]:
    """List all tables in the database"""
    with get_connection() as conn:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r[0] for r in result]


def describe_table(table_name: str) -> list[dict[str, Any]]:
    """Describe the schema of a table"""
    with get_connection() as conn:
        result = conn.execute(f"DESCRIBE {table_name}").fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in result]


def get_anomaly_by_id(anomaly_id: str) -> dict[str, Any] | None:
    """Get a specific anomaly by ID"""
    results = run_query(
        "SELECT * FROM detected_anomalies WHERE anomaly_id = $id",
        {"id": anomaly_id}
    )
    return results[0] if results else None


def get_all_anomalies() -> list[dict[str, Any]]:
    """Get all anomalies ordered by date"""
    return run_query(
        "SELECT * FROM detected_anomalies ORDER BY anomaly_date DESC"
    )


def get_device_by_hostname(hostname: str) -> dict[str, Any] | None:
    """Get device information by hostname"""
    results = run_query(
        "SELECT * FROM network_devices WHERE hostname = $hostname",
        {"hostname": hostname}
    )
    return results[0] if results else None


def get_devices_by_hostnames(hostnames: list[str]) -> list[dict[str, Any]]:
    """Get device information for multiple hostnames"""
    if not hostnames:
        return []
    
    placeholders = ", ".join([f"'{h}'" for h in hostnames])
    return run_query(
        f"SELECT * FROM network_devices WHERE hostname IN ({placeholders})"
    )


def get_telemetry_for_device(
    device_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """Get telemetry data for a device within a time range"""
    sql = "SELECT * FROM device_telemetry WHERE device_id = $device_id"
    params = {"device_id": device_id}
    
    if start_time:
        sql += " AND timestamp >= $start_time"
        params["start_time"] = start_time
    
    if end_time:
        sql += " AND timestamp <= $end_time"
        params["end_time"] = end_time
    
    sql += " ORDER BY timestamp DESC LIMIT $limit"
    params["limit"] = limit
    
    return run_query(sql, params)


def get_syslogs_for_device(
    device_id: str | None = None,
    hostname: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    severity: str | None = None,
    message_type: str | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """Get syslog entries for a device within a time range"""
    sql = "SELECT * FROM device_syslogs WHERE 1=1"
    params = {}
    
    if device_id:
        sql += " AND device_id = $device_id"
        params["device_id"] = device_id
    
    if hostname:
        sql += " AND hostname = $hostname"
        params["hostname"] = hostname
    
    if start_time:
        sql += " AND timestamp >= $start_time"
        params["start_time"] = start_time
    
    if end_time:
        sql += " AND timestamp <= $end_time"
        params["end_time"] = end_time
    
    if severity:
        sql += " AND severity = $severity"
        params["severity"] = severity
    
    if message_type:
        sql += " AND message_type = $message_type"
        params["message_type"] = message_type
    
    sql += " ORDER BY timestamp DESC LIMIT $limit"
    params["limit"] = limit
    
    return run_query(sql, params)


def search_syslogs_by_keyword(
    keyword: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 50
) -> list[dict[str, Any]]:
    """Search syslogs by keyword in the message"""
    sql = "SELECT * FROM device_syslogs WHERE message LIKE $keyword"
    params = {"keyword": f"%{keyword}%"}
    
    if start_time:
        sql += " AND timestamp >= $start_time"
        params["start_time"] = start_time
    
    if end_time:
        sql += " AND timestamp <= $end_time"
        params["end_time"] = end_time
    
    sql += " ORDER BY timestamp DESC LIMIT $limit"
    params["limit"] = limit
    
    return run_query(sql, params)


if __name__ == "__main__":
    """Test the database connection"""
    print("Testing DuckDB connection...")
    print("\nTables:", list_tables())
    
    for table in list_tables():
        print(f"\n{table}:")
        schema = describe_table(table)
        for col in schema:
            print(f"  {col}")
    
    print("\nTest query - all anomalies:")
    anomalies = get_all_anomalies()
    print(f"Found {len(anomalies)} anomalies")
    if anomalies:
        print(f"First anomaly: {anomalies[0]['anomaly_id']}")
