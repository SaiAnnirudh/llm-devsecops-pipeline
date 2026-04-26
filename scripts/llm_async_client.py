import os
import sys
import json
import urllib.request
import threading
import time
import re

# Shared dictionary to store results across threads safely
results = {}
results_lock = threading.Lock()

def map_error(code, raw_ext):
    if code == 429:
        return "HTTP 429: Quota Exceeded / Billing Empty"
    elif code == 403:
        return "HTTP 403: Forbidden - Invalid API Credentials"
    elif code == 404:
        return "HTTP 404: Not Found - Model or Endpoint unverified"
    return f"HTTP Error {code}: {raw_ext}"

def parse_llm_response(text):
    try:
        # Remove potential markdown formatting
        text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception:
        # Fallback if the LLM didn't return valid JSON
        return [{"file_path": "Unknown", "issue_title": "Unstructured Findings", "description": text, "original_code": "", "suggested_code_replacement": ""}]

def push_metrics_to_pushgateway(results_data):
    pushgateway_url = os.environ.get("PUSHGATEWAY_URL", "http://localhost:9091")
    try:
        job_name = "llm_devsecops_scan"
        metrics_data = f"llm_scan_last_success_time {time.time()}\n"
        for agent, info in results_data.items():
            status_val = 1 if info.get("status") == "success" else 0
            metrics_data += f'llm_agent_status{{agent="{agent}"}} {status_val}\n'
            
            findings = info.get("findings", [])
            if isinstance(findings, list):
                metrics_data += f'llm_agent_findings_count{{agent="{agent}"}} {len(findings)}\n'
                
        req = urllib.request.Request(
            f"{pushgateway_url}/metrics/job/{job_name}",
            data=metrics_data.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=5)
        print("[Metrics] Successfully pushed metrics to Pushgateway.")
    except Exception as e:
        print(f"[Metrics] Failed to push to Pushgateway: {e} (Is Pushgateway running?)")

def evaluate_with_gemini(prompt, api_key):
    try:
        if not api_key:
            return {"status": "skipped", "findings": "No API Key provided"}
            
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [{"parts": [{"text": "You are a DevSecOps LLM engine. " + prompt}]}]
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            res = json.loads(response.read().decode('utf-8'))
            findings_text = res['candidates'][0]['content']['parts'][0]['text']
            return {"status": "success", "findings": parse_llm_response(findings_text)}
    except urllib.error.HTTPError as he:
        return {"status": map_error(he.code, he.read().decode('utf-8')), "findings": None}
    except Exception as e:
        return {"status": "error", "findings": str(e)}

def run_evaluation(name, func, prompt, api_key):
    res = func(prompt, api_key)
    with results_lock:
        results[name] = res
    print(f"[LLM Scan] {name} evaluation complete. Status: {res['status']}")

def send_slack_alert(results_data):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[Slack] Webhook not configured/loaded. Skipping alert.")
        return

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🛡️ Phase 2: Async LLM Validation Engine",
                "emoji": True
            }
        }
    ]
    
    for agent, info in results_data.items():
        status = info.get("status", "Unknown")
        color = "🟢" if "success" in status.lower() else "🔴"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{color} {agent} Platform*\nStatus: `{status}`"
            }
        })
        
    slack_payload = {"blocks": blocks}
    
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(slack_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=10)
        print("[Slack] DevSecOps Alert successfully transmitted!")
    except Exception as e:
        print(f"[Slack] Failed to send alert: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_async_client.py <directory_to_scan>")
        sys.exit(1)

    scan_dir = sys.argv[1]
    
    # Generate Prompt Payload
    iac_content = ""
    for root, _, files in os.walk(scan_dir):
        for file in files:
                if file.endswith(('.tf', '.json', '.yaml', '.yml')) and not file.endswith('.tfstate'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            iac_content += f"\n\n--- File: {filepath} ---\n{f.read()}\n"
                    except Exception:
                        pass

    prompt = (
        "Review the following Infrastructure as Code for potential security vulnerabilities, misconfigurations, "
        "and compliance violations that static tools might miss. Focus on complex logic flaws.\n"
        "You MUST return your findings as a strict JSON array of objects. Do not include markdown code blocks (like ```json), just the raw JSON. "
        "Each object must have exactly these keys:\n"
        "- \"file_path\": The path to the file with the issue.\n"
        "- \"issue_title\": A short title for the vulnerability.\n"
        "- \"description\": Detailed explanation of the risk.\n"
        "- \"original_code\": The specific lines of code that are vulnerable.\n"
        "- \"suggested_code_replacement\": The exact code snippet to fix the issue.\n"
        f"\n{iac_content}"
    )

    print(f"[LLM Scan] Initiating Gemini validation on {scan_dir}...")

    # Gemini (gemini-1.5-flash)
    gemini_thread = threading.Thread(
        target=run_evaluation,
        args=("Gemini", evaluate_with_gemini, prompt, os.environ.get("GEMINI_API_KEY"))
    )
    gemini_thread.start()
    gemini_thread.join()

    # Write unified report
    with open("llm_validation_results.json", "w") as out:
        json.dump(results, out, indent=2)
        
    print("[Async Scan] Validations efficiently stored in llm_validation_results.json")
    
    # PHASE 2: Dispatch results to Slack
    send_slack_alert(results)
    
    # PHASE 3: Push metrics
    push_metrics_to_pushgateway(results)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
