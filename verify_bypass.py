import requests
import re

# URL
url = 'http://localhost:5000/auth/signup'

# Session
s = requests.Session()

# 1. Get the page to get CSRF token
print("Fetching signup page...")
r = s.get(url)
print(f"Status: {r.status_code}")

# Extract CSRF token
csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', r.text)
if not csrf_match:
    # Try alternative order
    csrf_match = re.search(r'<input[^>]*value="([^"]+)"[^>]*name="csrf_token"', r.text)

if not csrf_match:
    print("Error: CSRF token not found. Printing first 500 chars of response:")
    print(r.text[:500])
    exit(1)
csrf_token = csrf_match.group(1)
print(f"CSRF Token: {csrf_token}")

# 2. Submit form with bypass nonce
import time
unique_id = int(time.time())
data = {
    'csrf_token': csrf_token,
    'org_name': f'Bypass {unique_id}',
    'subdomain': f'bp-{unique_id}', # Keep under 20 chars (10 digits + 3 chars = 13)
    'address': '123 Bypass Lane',
    'first_name': 'Bypass',
    'last_name': 'Tester',
    'email': f'bypass_{unique_id}@test.com',
    'password': 'Password123!',
    'confirm_password': 'Password123!',
    'card_nonce': 'fake-nonce-bypass'
}

print("Submitting form with bypass nonce...")
r = s.post(url, data=data, allow_redirects=True)
print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")

if 'dashboard' in r.url or 'login' in r.url:
    print("SUCCESS: Redirected to dashboard/login")
else:
    print("FAILURE: Stuck on signup page")
    print("Response URL: " + r.url)
    print("Searching for errors...")
    
    # Simple search for error classes
    error_lines = []
    for line in r.text.split('\n'):
        if 'invalid-feedback' in line or 'alert-danger' in line or 'Please correct the errors' in line:
            error_lines.append(line.strip())
            
    if error_lines:
        print("Found validation errors:")
        for line in error_lines:
            print(line)
    else:
        print("No obvious validation errors found in HTML. Printing first 5000 chars:")
        print(r.text[:5000])
