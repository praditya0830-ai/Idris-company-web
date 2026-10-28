"""Website waitlist (gtm/perintah-website-waitlist-untuk-tim-solver.md): validation, storage, stats, privacy."""
import csv, io, os, tempfile
from datetime import datetime, timedelta, timezone
import waitlist

GOOD = {"name": "Ada Engineer", "email": "Ada@Example.com", "industry": "Automotive", "company_size": "Small (<50)",
        "design_partner": "yes", "consent": True, "utm_source": "linkedin", "utm_medium": "post", "fill_ms": 9000}


def _env(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setattr(os, "environ", {**os.environ, "IDRIS_DATA_DIR": d, "IDRIS_ADMIN_TOKEN": "tok"})
    waitlist._hits.clear()
    return d


def test_refuses_without_persistent_storage(monkeypatch):
    monkeypatch.setattr(os, "environ", {k: v for k, v in os.environ.items() if k != "IDRIS_DATA_DIR"})
    waitlist._hits.clear()
    c, b = waitlist.signup(dict(GOOD), "1.1.1.1")
    assert c == 503 and b["storage"] is False


def test_validation_and_consent(monkeypatch):
    _env(monkeypatch)
    c, b = waitlist.signup({**GOOD, "email": "nope", "consent": False, "industry": "Space"}, "1.1.1.2")
    assert c == 400 and set(b["fields"]) == {"email", "consent", "industry"}


def test_store_update_stats_export_delete(monkeypatch):
    _env(monkeypatch)
    assert waitlist.signup(dict(GOOD), "1.1.1.3")[0] == 200
    c, b = waitlist.signup({**GOOD, "company": "Acme", "design_partner": "maybe"}, "1.1.1.3")   # same e-mail: update
    assert c == 200 and b["updated"]
    waitlist.signup({**GOOD, "email": "b@corp.de", "industry": "Marine", "design_partner": "no", "utm_source": ""}, "1.1.1.4")
    waitlist.signup({**GOOD, "email": "qa1@test.idris"}, "1.1.1.5")                            # QA test: not counted
    waitlist.signup({**GOOD, "email": "bot@x.com", "website": "spam"}, "1.1.1.6")              # honeypot: dropped
    waitlist.signup({**GOOD, "email": "fast@x.com", "fill_ms": 300}, "1.1.1.7")                # too fast: dropped
    waitlist.visit({"utm_source": "LinkedIn"}); waitlist.visit({})
    s = waitlist.stats("tok")
    assert s["total_signups"] == 2 and s["new_last_7_days"] == 2 and s["test_signups_excluded"] == 1
    assert s["design_partner_yes_or_maybe"] == 1 and s["by_industry"] == {"Automotive": 1, "Marine": 1}
    assert s["signups_by_source"] == {"linkedin": 1, "direct": 1}
    assert s["visits_total"] == 2 and s["visits_by_source"] == {"linkedin": 1, "direct": 1}
    rows = list(csv.DictReader(io.StringIO(waitlist.export_csv("tok"))))
    assert [r["email"] for r in rows] == ["ada@example.com", "b@corp.de"] and rows[0]["company"] == "Acme"
    assert "ip" not in rows[0]
    assert waitlist.delete("tok", "qa1@test.idris")["deleted"] == 1
    try:
        waitlist.stats("wrong"); assert False
    except waitlist.WaitlistError as e:
        assert e.status == 403


def test_rate_limit(monkeypatch):
    _env(monkeypatch)
    codes = [waitlist.signup({**GOOD, "email": f"u{i}@x.com"}, "9.9.9.9")[0] for i in range(7)]
    assert codes[:5] == [200] * 5 and codes[5] == 429
