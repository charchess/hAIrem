import requests
import time
import sys
import os

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:8000")
MAX_ATTEMPTS = int(os.getenv("HEALTH_MAX_ATTEMPTS", "30"))
SLEEP_INTERVAL = int(os.getenv("HEALTH_SLEEP_INTERVAL", "1"))
TIMEOUT = int(os.getenv("HEALTH_TIMEOUT", "2"))

def check_health():
    print(f"Checking health at {BRIDGE_URL} (Max attempts: {MAX_ATTEMPTS})...")
    
    for i in range(MAX_ATTEMPTS):
        try:
            # 1. Check for agents
            agents_resp = requests.get(f"{BRIDGE_URL}/api/agents", timeout=TIMEOUT)
            if agents_resp.status_code == 200:
                agents = agents_resp.json()
                if len(agents) > 0:
                    print(f"✅ Found {len(agents)} agents.")
                    
                    # 2. Check for brain status
                    status_resp = requests.get(f"{BRIDGE_URL}/api/status", timeout=TIMEOUT)
                    if status_resp.status_code == 200:
                        status = status_resp.json()
                        brain_status = status.get("brain")
                        if brain_status == "online":
                            print("✅ BRAIN is online.")
                            return True
                        else:
                            print(f"⌛ Brain status: {brain_status}. Waiting...")
                    else:
                        print(f"⚠️ Status API returned {status_resp.status_code}")
                else:
                    print(f"⌛ No agents discovered yet. Waiting...")
            else:
                print(f"⚠️ Agents API returned {agents_resp.status_code}")
        except Exception as e:
            print(f"⌛ Bridge not reachable: {e}. Waiting...")
        
        time.sleep(SLEEP_INTERVAL)
    
    print(f"❌ Health check failed after {MAX_ATTEMPTS * SLEEP_INTERVAL} seconds.")
    return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
