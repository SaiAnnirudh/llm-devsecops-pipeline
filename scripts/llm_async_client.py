import os
import sys
import json
import urllib.request
import threading

def send_payload_async(payload, endpoint, api_key):
    """Sends the IaC payload asynchronously to the EC2 LLM engine."""
    def _send():
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"[Async Scan] Payload sent. Status: {response.getcode()}")
        except Exception as e:
            print(f"[Async Scan] Failed to send payload: {e}")
            
    thread = threading.Thread(target=_send)
    thread.start()
    return thread

def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_async_client.py <directory_to_scan>")
        sys.exit(1)

    scan_dir = sys.argv[1]
    api_key = os.environ.get("EC2_API_KEY", "dummy_key_if_not_set")
    # Replace with the actual EC2 endpoint URL
    endpoint = os.environ.get("EC2_LLM_ENDPOINT", "http://localhost:8080/scan")

    # A simple mock payload generator reading files in the directory
    payload = {"files": {}}
    for root, _, files in os.walk(scan_dir):
        for file in files:
            if file.endswith(('.tf', '.json', '.yaml', '.yml')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        payload["files"][filepath] = f.read()
                except Exception as e:
                    pass

    print(f"[Async Scan] Initiating async LLM scan on {scan_dir}...")
    # Trigger the asynchronous request
    send_payload_async(payload, endpoint, api_key)
    # Return 202 Accepted logic from the client script perspective
    print("[Async Scan] HTTP 202 Accepted. Engine will validate asynchronously.")
    sys.exit(0)

if __name__ == "__main__":
    main()
