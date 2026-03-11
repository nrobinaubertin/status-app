"""Status app Flask workload."""

import datetime
import os
import platform
import socket
import time
import uuid

import flask

app = flask.Flask(__name__)


@app.before_request
def before_request_timing():
    """Record the request start time.

    Store the start time in Flask's g for later diagnostics.
    """
    flask.g.start_time = time.perf_counter()


def get_memory_info_linux():
    """Parse /proc/meminfo on Linux systems.

    Return a dictionary with memory stats or an explanatory string when unavailable.
    """
    if platform.system() != "Linux":
        return "Not available on this OS"

    meminfo = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    # Key is the first part (e.g., "MemTotal:"), value is the second.
                    key = parts[0].replace(":", "")
                    # We are interested in these specific keys.
                    if key in ["MemTotal", "MemFree", "MemAvailable"]:
                        meminfo[key] = int(parts[1])  # Value is in kB
    except FileNotFoundError:
        return "Could not read /proc/meminfo"

    if not all(k in meminfo for k in ["MemTotal", "MemAvailable"]):
        return "Could not parse required memory fields"

    # Convert from kB to MB for readability
    total_mb = meminfo.get("MemTotal", 0) / 1024
    available_mb = meminfo.get("MemAvailable", 0) / 1024
    used_mb = total_mb - available_mb
    usage_percent = (used_mb / total_mb) * 100 if total_mb > 0 else 0

    return {
        "total_mb": round(total_mb, 2),
        "available_mb": round(available_mb, 2),
        "used_mb": round(used_mb, 2),
        "usage_percent": round(usage_percent, 2),
    }


@app.route("/")
def index():
    """Return system and request information as JSON."""
    # --- System Load (Unix-like only) ---
    system_load = "Not available on this OS"
    if hasattr(os, "getloadavg"):
        try:
            load_1, load_5, load_15 = os.getloadavg()
            system_load = {
                "1_min": round(load_1, 2),
                "5_min": round(load_5, 2),
                "15_min": round(load_15, 2),
            }
        except OSError:
            system_load = "Could not retrieve load average"

    # --- Memory Usage (Linux only) ---
    memory_usage = get_memory_info_linux()

    # --- Network Information ---
    # Get the IP address of the client making the request.
    # request.headers.get('X-Forwarded-For') is used to get the original IP if behind a proxy.
    remote_ip = flask.request.headers.get("X-Forwarded-For", flask.request.remote_addr)

    # Get the hostname of the server.
    hostname = socket.gethostname()

    # Get the IP address of the server.
    try:
        server_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        server_ip = "127.0.0.1"  # Fallback for environments where hostname isn't resolvable

    # --- Time Information ---
    # Get the current time in UTC.
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Format the time into a standard ISO 8601 string.
    time_utc_iso = now_utc.isoformat().replace("+00:00", "Z")

    # --- Request Information ---
    request_headers = dict(flask.request.headers)
    request_method = flask.request.method
    request_path = flask.request.path
    request_args = dict(flask.request.args)

    # --- System Information ---
    python_version = platform.python_version()
    system_info = f"{platform.system()} {platform.release()}"
    node_id = str(uuid.getnode())

    # --- Diagnostics ---
    # Calculate the total time taken to process the request inside the app.
    processing_time_ms = (time.perf_counter() - flask.g.start_time) * 1000

    # --- Assemble the response data ---
    # We use a dictionary to structure the data, which will be converted to JSON.
    response_data = {
        "client": {
            "ip_address": remote_ip,
        },
        "server": {
            "hostname": hostname,
            "ip_address": server_ip,
            "datetime_utc": time_utc_iso,
            "node_id": node_id,
            "system_load_avg": system_load,
            "memory_usage": memory_usage,
        },
        "request": {
            "method": request_method,
            "path": request_path,
            "arguments": request_args,
            "headers": request_headers,
        },
        "environment": {
            "python_version": python_version,
            "system": system_info,
        },
        "diagnostics": {"request_processing_duration_ms": round(processing_time_ms, 4)},
    }

    # Use jsonify to properly format the dictionary as a JSON response
    # with the correct Content-Type header.
    return flask.jsonify(response_data)


if __name__ == "__main__":
    app.run()
