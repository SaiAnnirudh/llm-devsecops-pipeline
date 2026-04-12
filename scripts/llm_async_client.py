import os
import sys
import json
import urllib.request
import threading

# Shared dictionary to store results across threads safely
results = {}
results_lock = threading.Lock()

def evaluate_with_openai(prompt, api_key):
    try:
        if not api_key:
            return {"status": "skipped", "findings": "No API Key provided"}
        
        endpoint = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a DevSecOps LLM engine."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return {"status": "success", "findings": res['choices'][0]['message']['content']}
    except urllib.error.HTTPError as he:
        return {"status": f"HTTP Error {he.code}", "findings": he.read().decode('utf-8')}
    except Exception as e:
        return {"status": "error", "findings": str(e)}

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
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return {"status": "success", "findings": res['candidates'][0]['content']['parts'][0]['text']}
    except urllib.error.HTTPError as he:
        return {"status": f"HTTP Error {he.code}", "findings": he.read().decode('utf-8')}
    except Exception as e:
        return {"status": "error", "findings": str(e)}

def evaluate_with_groq(prompt, api_key):
    try:
        if not api_key:
            return {"status": "skipped", "findings": "No API Key provided"}
            
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a DevSecOps LLM engine."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return {"status": "success", "findings": res['choices'][0]['message']['content']}
    except urllib.error.HTTPError as he:
        return {"status": f"HTTP Error {he.code}", "findings": he.read().decode('utf-8')}
    except Exception as e:
        return {"status": "error", "findings": str(e)}

def run_evaluation(name, func, prompt, api_key):
    res = func(prompt, api_key)
    with results_lock:
        results[name] = res
    print(f"[LLM Scan] {name} evaluation complete. Status: {res['status']}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_async_client.py <directory_to_scan>")
        sys.exit(1)

    scan_dir = sys.argv[1]
    
    # Generate Prompt Payload
    iac_content = ""
    for root, _, files in os.walk(scan_dir):
        for file in files:
            if file.endswith(('.tf', '.json', '.yaml', '.yml')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        iac_content += f"\n\n--- File: {filepath} ---\n{f.read()}\n"
                except Exception:
                    pass

    prompt = (
        "Review the following Infrastructure as Code for potential security vulnerabilities, misconfigurations, "
        "and compliance violations that static tools might miss. Focus on complex logic flaws.\n"
        f"{iac_content}"
    )

    print(f"[LLM Scan] Initiating async ensemble validation on {scan_dir}...")
    
    threads = []
    
    # 1. OpenAI (gpt-3.5-turbo)
    t1 = threading.Thread(target=run_evaluation, args=("OpenAI", evaluate_with_openai, prompt, os.environ.get("OPENAI_API_KEY")))
    threads.append(t1)
    
    # 2. Gemini (gemini-1.5-flash)
    t2 = threading.Thread(target=run_evaluation, args=("Gemini", evaluate_with_gemini, prompt, os.environ.get("GEMINI_API_KEY")))
    threads.append(t2)
    
    # 3. Groq (llama3-8b-8192)
    t3 = threading.Thread(target=run_evaluation, args=("Groq", evaluate_with_groq, prompt, os.environ.get("GROQ_API_KEY")))
    threads.append(t3)

    for t in threads:
        t.start()
        
    for t in threads:
        t.join()

    # Write unified report
    with open("llm_validation_results.json", "w") as out:
        json.dump(results, out, indent=2)

    print("[Async Scan] Validations efficiently stored in llm_validation_results.json")
    sys.exit(0)

if __name__ == "__main__":
    main()
