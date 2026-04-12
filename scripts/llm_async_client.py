import os
import sys
import json
import urllib.request
import threading

def evaluate_with_openai_async(payload, api_key):
    """Sends the IaC payload to OpenAI GPT-4 asynchronously for deep validation."""
    def _send():
        try:
            endpoint = "https://api.openai.com/v1/chat/completions"
            # Format the payload to a text representation of the IaC
            iac_content = ""
            for filepath, content in payload["files"].items():
                iac_content += f"\n\n--- File: {filepath} ---\n{content}\n"
            
            prompt = (
                "You are an expert Cloud Security Architect. Review the following "
                "Infrastructure as Code for potential security vulnerabilities, misconfigurations, "
                "and compliance violations that static tools might miss. Focus on complex logic flaws.\n"
                f"{iac_content}"
            )
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a DevSecOps LLM engine."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                print("[LLM Scan] Open AI Validation complete. Findings:")
                print(result['choices'][0]['message']['content'])
                
                # Write to output JSON as per Phase 1 requirements
                with open("llm_validation_results.json", "w") as out:
                    json.dump(result, out, indent=2)
                    
        except Exception as e:
            print(f"[LLM Scan] Failed to evaluate payload with OpenAI: {e}")
            
    thread = threading.Thread(target=_send)
    thread.start()
    return thread

def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_async_client.py <directory_to_scan>")
        sys.exit(1)

    scan_dir = sys.argv[1]
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("[LLM Scan] OPENAI_API_KEY not found in environment, proceeding without LLM validation.")
        sys.exit(0)

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

    print(f"[LLM Scan] Initiating async OpenAI GPT validation on {scan_dir}...")
    # Trigger the asynchronous request
    thread = evaluate_with_openai_async(payload, api_key)
    # Wait for completion just for this demo, usually it would just exit
    thread.join()
    # Return 202 Accepted logic from the client script perspective
    print("[Async Scan] HTTP 202 Accepted. Engine will validate asynchronously.")
    sys.exit(0)

if __name__ == "__main__":
    main()
