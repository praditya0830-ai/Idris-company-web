"""Token-protected admin page: the waitlist as a table, with a CSV download button.

Rendered on the server from the same data as /waitlist/export.csv, so the page never
calls an API with the token from the browser. Everything shown here is escaped.
"""
import html
from datetime import datetime

CSS = """
:root{--bg:#09090B;--panel:#121217;--panel2:#0E0E12;--line:rgba(255,255,255,.1);--soft:rgba(255,255,255,.055);
--text:#F2F3F5;--muted:#9A9AA6;--dim:#6E6E7A;--cyan:#00E5FF;--amber:#F5B849;--rose:#FF7A9A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased}
a{color:var(--cyan)}
.wrap{max-width:1280px;margin:0 auto;padding:28px 24px 60px}
header{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding-bottom:18px;border-bottom:1px solid var(--soft)}
.logo{display:flex;align-items:center;gap:10px;font-size:14px;letter-spacing:.3em;font-weight:500}
.logo b{color:var(--cyan);font-weight:600;letter-spacing:.28em}
.sub{font-size:12.5px;color:var(--dim);margin-left:auto;letter-spacing:.02em}
h1{font-size:26px;margin:26px 0 6px;letter-spacing:-.02em;font-weight:600}
.lead{color:var(--muted);font-size:14px;margin:0 0 20px}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--cyan);color:#06171B;font-weight:600;
font-size:13.5px;padding:10px 16px;border-radius:9px;text-decoration:none;white-space:nowrap}
.btn:hover{background:#5FEFFF}
.btn.ghost{background:transparent;color:#BFF6FF;border:1px solid rgba(0,229,255,.45);font-weight:500}
.btn.ghost:hover{background:rgba(0,229,255,.1)}
.bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.stats{display:flex;gap:8px;flex-wrap:wrap}
.stat{background:var(--panel);border:1px solid var(--soft);border-radius:10px;padding:8px 13px;font-size:12.5px;color:var(--muted)}
.stat b{color:var(--text);font-weight:600;font-size:14px;margin-left:6px}
.search{flex:1;min-width:200px}
input[type=search]{width:100%;font:inherit;font-size:13.5px;color:var(--text);background:var(--panel);
border:1px solid var(--line);border-radius:9px;padding:9px 13px}
input[type=search]:focus{outline:none;border-color:rgba(0,229,255,.5);box-shadow:0 0 0 3px rgba(0,229,255,.1)}
.tablewrap{border:1px solid var(--soft);border-radius:12px;overflow:auto;background:var(--panel2);max-height:70vh}
table{width:100%;border-collapse:collapse;font-size:13.2px;min-width:1000px}
th{position:sticky;top:0;z-index:1;background:#14141A;text-align:left;font-size:10.5px;letter-spacing:.14em;
text-transform:uppercase;color:#5E5E6A;font-weight:500;padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 14px;border-bottom:1px solid var(--soft);vertical-align:top}
tbody tr:hover{background:rgba(255,255,255,.022)}
tbody tr:last-child td{border-bottom:0}
.mail{color:#DDE0E6;text-decoration:none}
.mail:hover{color:var(--cyan)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;color:#A9ABB6;white-space:nowrap}
.dim{color:var(--dim)}
.badge{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;
border-radius:999px;border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.badge.yes{color:#06171B;background:var(--cyan);border-color:var(--cyan);font-weight:600}
.badge.maybe{color:var(--amber);border-color:rgba(245,184,73,.4);background:rgba(245,184,73,.08)}
.badge.no{color:#8A8A96}
.empty{padding:48px 20px;text-align:center;color:var(--dim);font-size:14px}
.note{margin-top:16px;font-size:12.5px;color:var(--dim);line-height:1.7}
.note code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:#B9BCC6;
background:rgba(255,255,255,.04);padding:2px 6px;border-radius:5px}
.err{max-width:640px;margin:80px auto;padding:26px 28px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
.err h1{margin-top:0;font-size:20px}
.err p{color:var(--muted);font-size:14px;margin:8px 0 0}
@media(max-width:700px){.wrap{padding:20px 16px 40px}h1{font-size:21px}.sub{margin-left:0}}
"""


def _e(value):
    return html.escape("" if value is None else str(value))


def _when(raw):
    """2026-11-15T11:20:15+00:00 -> 15 Nov 2026, 18:20 UTC (short, sortable enough)."""
    try:
        d = datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return _e(raw)
    return d.strftime("%d %b %Y") + '<br><span class="dim">' + d.strftime("%H:%M") + "</span>"


def _source(row):
    return row.get("utm_source") or row.get("ref") or "direct"


def _row_html(r):
    partner = (r.get("design_partner") or "").lower()
    badge_class = partner if partner in ("yes", "maybe", "no") else "no"
    email = r.get("email") or ""
    company = r.get("company") or ""
    role = r.get("role") or ""
    who = "<br>".join(x for x in (_e(company), '<span class="dim">%s</span>' % _e(role) if role else "") if x)
    return (
        "<tr>"
        '<td class="mono">%s</td>'
        "<td>%s</td>"
        '<td><a class="mail" href="mailto:%s">%s</a></td>'
        "<td>%s</td>"
        "<td>%s</td>"
        "<td>%s</td>"
        '<td><span class="badge %s">%s</span></td>'
        "<td>%s</td>"
        '<td class="dim">%s</td>'
        "</tr>"
        % (
            _when(r.get("created_at")),
            _e(r.get("name")) or '<span class="dim">—</span>',
            _e(email),
            _e(email),
            who or '<span class="dim">—</span>',
            _e(r.get("industry")) or '<span class="dim">—</span>',
            _e(r.get("company_size")) or '<span class="dim">—</span>',
            badge_class,
            _e(partner) or "—",
            _e(r.get("country")) or '<span class="dim">—</span>',
            _e(_source(r)),
        )
    )


def render(rows, token, include_test=False):
    yes = sum(1 for r in rows if r.get("design_partner") == "yes")
    maybe = sum(1 for r in rows if r.get("design_partner") == "maybe")
    no = sum(1 for r in rows if r.get("design_partner") == "no")
    token_q = html.escape(token, quote=True)
    csv_url = "/waitlist/export.csv?token=" + token_q + ("&include_test=1" if include_test else "")
    if include_test:
        toggle = '<a href="/admin?token=%s">sembunyikan email uji</a>' % token_q
    else:
        toggle = '<a href="/admin?token=%s&include_test=1">tampilkan email uji</a>' % token_q
    prefix = "" if include_test else " (email uji tidak ditampilkan)"
    body_rows = "".join(_row_html(r) for r in rows)
    table = (
        '<div class="tablewrap"><table>'
        "<thead><tr><th>Tanggal</th><th>Nama</th><th>Email</th><th>Perusahaan / Peran</th>"
        "<th>Industri</th><th>Ukuran</th><th>Design Partner</th><th>Negara</th><th>Sumber</th></tr></thead>"
        '<tbody id="rows">%s</tbody></table></div>' % body_rows
        if rows
        else '<div class="tablewrap"><div class="empty">Belum ada yang mendaftar.</div></div>'
    )
    return """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>IDRIS · Pendaftar waitlist</title>
<style>%s</style>
</head>
<body>
<div class="wrap">
  <header>
    <span class="logo"><b>IDRIS</b> ADMIN</span>
    <span class="sub">Halaman internal · jangan dibagikan</span>
  </header>

  <h1>Pendaftar waitlist</h1>
  <p class="lead">%d orang%s. Data ini sama persis dengan isi file CSV.</p>

  <div class="bar">
    <span class="stats">
      <span class="stat">Total<b>%d</b></span>
      <span class="stat">Design Partner: yes<b>%d</b></span>
      <span class="stat">maybe<b>%d</b></span>
      <span class="stat">no<b>%d</b></span>
    </span>
    <span class="search"><input type="search" id="q" placeholder="Cari nama, email, perusahaan, industri…" aria-label="Cari pendaftar"></span>
    <a class="btn" href="%s" download>Unduh CSV</a>
  </div>

  %s

  <p class="note">
    %s · Email uji (<code>@test.idris</code>) tidak ikut dihitung di statistik.<br>
    Menghapus satu orang (permintaan privasi): <code>POST /waitlist/delete</code> dengan
    <code>{"token":"…","email":"…"}</code>. Token yang sama juga membuka
    <code>/waitlist/export.csv</code> dan <code>/waitlist/stats</code>.
  </p>
</div>
<script>
(function(){
  var q = document.getElementById('q'), rows = [].slice.call(document.querySelectorAll('#rows tr'));
  if (q) q.addEventListener('input', function(){
    var v = q.value.trim().toLowerCase();
    rows.forEach(function(tr){ tr.style.display = !v || tr.textContent.toLowerCase().indexOf(v) > -1 ? '' : 'none'; });
  });
})();
</script>
</body>
</html>""" % (
        CSS,
        len(rows),
        prefix,
        len(rows), yes, maybe, no,
        html.escape(csv_url, quote=True),
        table,
        toggle,
    )


def render_error(status, message):
    hint = {
        403: "Token salah atau belum diisi. Buka halaman ini dengan <code>?token=…</code> yang sama dengan "
             "variabel <code>IDRIS_ADMIN_TOKEN</code> di server.",
        503: "Admin belum dikonfigurasi. Set variabel <code>IDRIS_ADMIN_TOKEN</code> (dan "
             "<code>IDRIS_DATA_DIR</code> ke disk permanen) di server, lalu buka lagi.",
    }.get(status, "Permintaan tidak bisa diproses.")
    return """<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>IDRIS · Tidak bisa dibuka</title><style>%s</style></head>
<body><div class="err">
<span class="logo"><b>IDRIS</b> ADMIN</span>
<h1>Halaman admin tidak bisa dibuka (%d)</h1>
<p>%s</p>
<p style="margin-top:14px"><code>%s</code></p>
</div></body></html>""" % (CSS, status, hint, _e(message))
