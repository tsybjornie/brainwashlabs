import requests

BASE_URL = "https://brainwashlabs.onrender.com"

def test_endpoint(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "POST":
            r = requests.post(url, json=data)
        else:
            r = requests.get(url)
        print(f"🧩 {path} → {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"❌ {path} → ERROR: {e}")

# Run tests
print("\n🚀 Testing Brainwash Labs API endpoints...\n")

test_endpoint("/auth/signup", "POST", {"email": "test@labs.com", "password": "12345"})
test_endpoint("/avatar/create", "POST", {"name": "Miki", "role": "Analyst"})
test_endpoint("/integrations/status", "GET")
test_endpoint("/healthz", "GET")

print("\n✅ Test complete.\n")
