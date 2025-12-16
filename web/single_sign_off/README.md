# Single Sign Off / \ Web

- CTF: NiteCTF 2025
- Category: Web
- Author: -
- Solver: .M4K5
- Flag: `nite{fake_flag}`

---

## Challenge
> "Our organization made a new Single Sign-On portal because we thought it would make everything easier. All our secrets are now locked away securely!"

The challenge involves exploiting a Document Portal that fetches URLs to access a protected Vault service sharing the same environment.

---

## Overview
- **Scheme**: A `fetcher` binary retrieves URLs. Internal services (`nite-vault`) are protected by a blocklist and Nginx routing.
- **Vulnerability**: The fetcher has a hostname check bypass. `curl` (used internally) leaks credentials from `.netrc` in verbose mode and automatically decodes URL-encoded hostnames.
- **Problem Type**: **SSRF & Credential Leak**. Chaining a blocklist bypass with a side-channel credential leak to access an internal service.

---

## Root Cause
The `fetcher` logic incorrectly whitelists `nite-sso`, allowing `curl` to connect and leak `.netrc` credentials via `stderr` (verbose output). Additionally, `curl` decodes `%2d` in `nite%2dvault` to `-` *after* the blocklist check but *before* resolution, allowing access to the blocked `nite-vault` hostname (Resolve: 127.0.0.1).

---

## Exploitation Steps
1. **Credential Leak**:
   - The document portal's `fetcher` uses `curl` in verbose mode, which leaks credentials from `.netrc` when connecting to `nite-sso`.
   - By creating a request to `http://nite-sso`, we can extract `NITE_USER` and `NITE_PASSWORD`.

2. **Redirect Chain Bypass**:
   - The `fetcher` blocks direct access to `nite-vault`, but the check can be bypassed using a redirect chain that triggers `CURLE_TOO_MANY_REDIRECTS`.
   - Use `nite-sso`'s `/doLogin` endpoint to create a chain of 5 redirects. Use an authenticated session (via registration) or the leaked credentials to authenticate the redirector to `nite-sso`.
   - The final redirect points to `nite-vault` (e.g., `http://nite%2dvault/...`) which `fetcher` executes without security checks after the limit is reached.

3. **PID Prediction & File Access**:
   - Use the bypass to read `/proc/self/status` via `nite-vault`'s `/view` endpoint (using leaked credentials).
   - Extract the `PID` of the process.
   - Replicate the Vault's filename generation algorithm: `sha256(random(seed=pid+uid+gid))`.
   - Use the bypass again to read the flag from the hidden file: `/app/nite-vault/secrets/<hash>.txt`.

4. **Flag**:
   `nite{fake_flag}`

---
