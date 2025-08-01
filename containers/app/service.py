#!/usr/bin/env python3
"""
New service example
"""

import time
import random
import asyncio
import os
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import ldclient
from ldclient.config import Config
from ldclient import LDClient, Context

CONFIG_DEFAULTS = {
    "name": "service-name",
    "version": "1.0.0",
    "failure_rate": 0.50,
    "latency": {
        "min_ms": 30,
        "max_ms": 60
    }
}

def merge_configs(file_config, defaults):
    """Recursively merge file config with defaults, preferring file values."""
    if not isinstance(file_config, dict):
        return file_config

    result = defaults.copy()
    for key, value in file_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(value, result[key])
        else:
            result[key] = value
    return result

def load_config(config_path="blue.yaml"):
    """Load configuration from YAML file and merge with defaults."""
    try:
        with open(config_path, 'r') as file:
            file_config = yaml.safe_load(file)
            if file_config is None:
                file_config = {}
            return merge_configs(file_config, CONFIG_DEFAULTS)
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found, using defaults")
        return CONFIG_DEFAULTS

# Global config variable
config = CONFIG_DEFAULTS

# Initialize LaunchDarkly client
ld_client = None

def init_launchdarkly():
    """Initialize LaunchDarkly client."""
    global ld_client
    sdk_key_file = os.getenv("LAUNCHDARKLY_SDK_KEY_FILE")
    if sdk_key_file:
        with open(sdk_key_file, "r") as file:
            sdk_key = file.read().strip()
    else:
        sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")

    if sdk_key:
        ldclient.set_config(Config(sdk_key))
        ld_client = ldclient.get()
        print(f"LaunchDarkly client initialized with SDK key: {sdk_key[:8]}...")
    else:
        print("Warning: LAUNCHDARKLY_SDK_KEY not set, LaunchDarkly metrics disabled")

def send_metric(is_error: bool, request_id: str = None):
    """Send metric to LaunchDarkly."""
    if ld_client:
        try:
            # Create context based on whether we have a request ID
            context = {
                "key": request_id,
                "kind": "request",
                "service": config["name"]
            }
            if request_id:
                # Create a request context with the request ID as the key
                context = Context.from_dict(context)
            else:
                # Fallback to service-metrics context
                context = Context.builder("service-metrics").set("service", config["name"]).build()

            # Send metric event
            if is_error:
                ld_client.track("http-errors", context, data={"service": config["name"]}, metric_value=1)
                ld_client.flush()
        except Exception as e:
            print(f"Error sending metric to LaunchDarkly: {e}")

app = FastAPI(title="Service")

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": config["name"],
            "version": config["version"],
            "timestamp": time.time()
        },
        status_code=200
    )

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def process_request(request: Request, path: str = ""):
    """Process any request with artificial latency."""

    # Get config values
    failure_rate = config["failure_rate"]
    min_latency = config["latency"]["min_ms"] / 1000.0
    max_latency = config["latency"]["max_ms"] / 1000.0
    service_name = config["name"]
    service_version = config["version"]

    # Get the X-LD-Request-Id header
    request_id = request.headers.get("X-LD-Request-Id")

    # Simulate service latency
    latency = random.uniform(min_latency, max_latency)
    await asyncio.sleep(latency)

    print(f"Request ID: {request_id}")
    print(request.headers)

    # Simulate configurable chance of failure
    if random.random() < failure_rate:
        # Send error metric with request ID
        send_metric(is_error=True, request_id=request_id)

        return JSONResponse(
            content={
                "service": service_name,
                "version": service_version,
                "http_status": 500,
                "error": "Error!"
            },
            status_code=500
        )

    # Get request details
    method = request.method
    headers = dict(request.headers)
    body = await request.body()

    # Send success metric with request ID
    send_metric(is_error=False, request_id=request_id)

    # Return response
    return JSONResponse(
        content={
            "service": service_name,
            "version": service_version,
            "http_status": 200,
            "message": "Success!"
        },
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn

    # Load configuration
    config_path = os.getenv("CONFIG_PATH", "blue.yaml")
    loaded_config = load_config(config_path)
    config.clear()
    config.update(loaded_config)

    # Initialize LaunchDarkly
    init_launchdarkly()

    port = int(os.getenv("PORT", 8080))
    print(f"Starting New Service on http://localhost:{port}")
    print(f"Configuration loaded: failure_rate={config['failure_rate']}, latency={config['latency']['min_ms']}-{config['latency']['max_ms']}ms")
    uvicorn.run(app, host="0.0.0.0", port=port)
