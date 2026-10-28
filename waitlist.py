"""Waitlist and design-partner sign-ups for the company website (gtm/perintah-website-waitlist-untuk-tim-solver.md).

Storage: SQLite on a persistent disk. The Render filesystem is wiped on every deploy, so nothing is stored
unless IDRIS_DATA_DIR points at a mounted persistent disk (e.g. /var/data). Without it every sign-up is
refused with 503 and the website shows a fallback, so no sign-up is ever silently lost.

Admin (Arya only): IDRIS_ADMIN_TOKEN must be set; pass it as ?token=… (export, stats, delete).
Privacy: no cookies, no IP address stored (the IP is used in memory for rate limiting only).
Test sign-ups (field test=true or an e-mail ending in @test.idris) are stored but never counted.
"""
import csv
import io
import os
import re
import sqlite3
import threading
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone

INDUSTRIES = ["Aerospace / drone / eVTOL", "Automotive", "Marine", "Industrial machinery", "Robotics", "Energy", "Other"]
COMPANY_SIZES = ["Solo / startup", "Small (<50)", "Medium (50–500)", "Large (>500)"]
PARTNER = ["yes", "maybe", "no"]
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[A-Za-z]{2,}$")
FIELDS = ["created_at", "name", "email", "company", "role", "industry", "company_size", "components",
          "design_partner", "country", "consent", "utm_source", "utm_medium", "utm_campaign", "ref", "is_test"]
MAX_LEN = {"name": 120, "email": 160, "company": 160, "role": 120, "components": 600, "country": 80,
           "utm_source": 80, "utm_medium": 80, "utm_campaign": 120, "ref": 120}
RATE = (5, 3600.0)                  # sign-ups per IP per hour
MIN_FILL_MS = 2500                  # faster than this is a bot
_lock = threading.Lock()
_hits = defaultdict(deque)


class WaitlistError(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status = status


def _db_path():
    d = os.environ.get("IDRIS_DATA_DIR", "").strip()
    if not d:
        return None
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "waitlist.sqlite3")


def _connect():
    p = _db_path()
    if not p:
        raise WaitlistError(503, "waitlist storage is not configured on this server (IDRIS_DATA_DIR)")
    con = sqlite3.connect(p, timeout=10)
    con.execute("""CREATE TABLE IF NOT EXISTS signups (
        email TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT, name TEXT, company TEXT, role TEXT,
        industry TEXT, company_size TEXT, components TEXT, design_partner TEXT, country TEXT, consent INTEGER,
        utm_source TEXT, utm_medium TEXT, utm_campaign TEXT, ref TEXT, is_test INTEGER)""")
    con.execute("CREATE TABLE IF NOT EXISTS visits (day TEXT, source TEXT, n INTEGER, PRIMARY KEY (day, source))")
    return con


def status():
    return {"storage_configured": _db_path() is not None, "admin_configured": bool(os.environ.get("IDRIS_ADMIN_TOKEN"))}


def _clean(v, k):
    s = ("" if v is None else str(v)).strip()
    return s[:MAX_LEN.get(k, 200)]


def _rate_ok(ip):
    now = time.time()
    with _lock:
        q = _hits[ip]
        while q and now - q[0] > RATE[1]:
            q.popleft()
        if len(q) >= RATE[0]:
            return False
        q.append(now)
        return True


def validate(p):
    r = {k: _clean(p.get(k), k) for k in MAX_LEN}
    r["email"] = r["email"].lower()
    errors = {}
    if not r["name"]:
        errors["name"] = "Please enter your name."
    if not EMAIL_RE.match(r["email"]):
        errors["email"] = "Please enter a valid work e-mail."
    r["industry"] = _clean(p.get("industry"), "industry")
    if r["industry"] not in INDUSTRIES:
        errors["industry"] = "Please choose an industry."
    r["company_size"] = _clean(p.get("company_size"), "company_size")
    if r["company_size"] not in COMPANY_SIZES:
        errors["company_size"] = "Please choose a company size."
    r["design_partner"] = _clean(p.get("design_partner"), "design_partner").lower()
    if r["design_partner"] not in PARTNER:
        errors["design_partner"] = "Please answer the design partner question."
    if p.get("consent") is not True:
        errors["consent"] = "Please tick the consent box so we may store your details."
    r["consent"] = 1
    r["is_test"] = 1 if (p.get("test") is True or r["email"].endswith("@test.idris")) else 0
    return r, errors


def signup(p, ip):
    """Returns (status, body). Bots get a normal-looking success and nothing is stored."""
    if _clean(p.get("website"), "website") or (isinstance(p.get("fill_ms"), (int, float)) and p["fill_ms"] < MIN_FILL_MS):
        return 200, {"success": True}
    if not _rate_ok(ip or "?"):
        return 429, {"success": False, "error": "Too many sign-ups from this connection. Please try again later."}
    r, errors = validate(p)
    if errors:
        return 400, {"success": False, "error": "Please check the highlighted fields.", "fields": errors}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        con = _connect()
    except WaitlistError as e:
        return e.status, {"success": False, "error": str(e), "storage": False}
    with con:
        old = con.execute("SELECT created_at FROM signups WHERE email = ?", (r["email"],)).fetchone()
        con.execute("""INSERT OR REPLACE INTO signups (email, created_at, updated_at, name, company, role, industry,
            company_size, components, design_partner, country, consent, utm_source, utm_medium, utm_campaign, ref, is_test)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r["email"], old[0] if old else now, now, r["name"], r["company"], r["role"], r["industry"],
                     r["company_size"], r["components"], r["design_partner"], r["country"], 1, r["utm_source"],
                     r["utm_medium"], r["utm_campaign"], r["ref"], r["is_test"]))
    con.close()
    return 200, {"success": True, "updated": bool(old), "design_partner": r["design_partner"]}


def visit(p):
    """Anonymous page-view counter per day and source. No cookie, no IP, no user agent."""
    src = _clean(p.get("utm_source") or p.get("ref") or "direct", "utm_source").lower() or "direct"
    day = datetime.now(timezone.utc).date().isoformat()
    try:
        con = _connect()
    except WaitlistError:
        return 200, {"success": True, "stored": False}
    with con:
        con.execute("INSERT INTO visits (day, source, n) VALUES (?, ?, 1) "
                    "ON CONFLICT(day, source) DO UPDATE SET n = n + 1", (day, src))
    con.close()
    return 200, {"success": True}


def _authorised(token):
    want = os.environ.get("IDRIS_ADMIN_TOKEN", "")
    if not want:
        raise WaitlistError(503, "admin access is not configured on this server (IDRIS_ADMIN_TOKEN)")
    if not token or token != want:
        raise WaitlistError(403, "wrong or missing token")


def _rows(con, include_test=False):
    cur = con.execute("SELECT " + ", ".join(FIELDS) + " FROM signups" + ("" if include_test else " WHERE is_test = 0")
                      + " ORDER BY created_at")
    return [dict(zip(FIELDS, row)) for row in cur.fetchall()]


def export_csv(token, include_test=False):
    _authorised(token)
    con = _connect()
    rows = _rows(con, include_test)
    con.close()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def stats(token, now=None):
    """Weekly numbers for Arya, exactly as stored: test sign-ups excluded, nothing rounded."""
    _authorised(token)
    con = _connect()
    rows = _rows(con)
    visits = con.execute("SELECT day, source, n FROM visits").fetchall()
    tests = con.execute("SELECT COUNT(*) FROM signups WHERE is_test = 1").fetchone()[0]
    con.close()
    now = now or datetime.now(timezone.utc)
    week = (now - timedelta(days=7)).isoformat(timespec="seconds")
    src = Counter((r["utm_source"] or r["ref"] or "direct").lower() for r in rows)
    vday = [v for v in visits if v[0] >= (now - timedelta(days=7)).date().isoformat()]
    return {"total_signups": len(rows), "new_last_7_days": sum(r["created_at"] >= week for r in rows),
            "design_partner": dict(Counter(r["design_partner"] for r in rows)),
            "design_partner_yes_or_maybe": sum(r["design_partner"] in ("yes", "maybe") for r in rows),
            "by_industry": dict(Counter(r["industry"] for r in rows).most_common()),
            "by_company_size": dict(Counter(r["company_size"] for r in rows).most_common()),
            "signups_by_source": dict(src.most_common()),
            "visits_total": sum(v[2] for v in visits), "visits_last_7_days": sum(v[2] for v in vday),
            "visits_by_source": dict(_sum_by_source(visits).most_common()),
            "test_signups_excluded": tests,
            "as_of": now.isoformat(timespec="seconds")}


def _sum_by_source(visits):
    c = Counter()
    for _, s, n in visits:
        c[s] += n
    return c


def delete(token, email):
    """GDPR erasure (or removing QA test sign-ups)."""
    _authorised(token)
    con = _connect()
    with con:
        n = con.execute("DELETE FROM signups WHERE email = ?", (_clean(email, "email").lower(),)).rowcount
    con.close()
    return {"success": True, "deleted": n}


def options():
    return {"industries": INDUSTRIES, "company_sizes": COMPANY_SIZES, "design_partner": PARTNER, **status()}
