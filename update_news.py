#!/usr/bin/env python3
"""Descarga titulares reales de los feeds RSS/Atom y escribe news.json.
No inventa nada: solo guarda lo que cada medio publica (titulo, resumen del medio, imagen, enlace)."""
import json, re, html, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasCatolicasBot/1.0)"}
PER_SOURCE = 8

# Si un feed cambia de direccion, edita solo esta lista.
SOURCES = [
 {"id":"aciprensa","name":"ACI Prensa","group":"Iglesia","home":"https://www.aciprensa.com","feeds":["https://www.aciprensa.com/rss"],"catholic":True},
 {"id":"ewtn","name":"EWTN Noticias","group":"Iglesia","home":"https://www.ewtnnoticias.com","feeds":["https://www.ewtnnoticias.com/rss"],"catholic":True},
 {"id":"semana","name":"Semana","group":"Colombia","home":"https://www.semana.com","feeds":["https://www.semana.com/arc/outboundfeeds/rss/?outputType=xml"]},
 {"id":"eltiempo","name":"El Tiempo","group":"Colombia","home":"https://www.eltiempo.com","feeds":["https://www.eltiempo.com/rss/colombia.xml"]},
 {"id":"citytv","name":"Citytv","group":"Colombia","home":"https://citytv.com.co","feeds":["https://citytv.com.co/feed/"]},
 {"id":"infobae","name":"Infobae","group":"Mundo","home":"https://www.infobae.com","feeds":["https://www.infobae.com/arc/outboundfeeds/rss/"]},
 {"id":"rtve","name":"TVE (RTVE)","group":"Mundo","home":"https://www.rtve.es/noticias/","feeds":["https://www.rtve.es/api/noticias.rss"]},
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def discover(home):
    """Si el feed falla, busca el feed oficial anunciado en la portada del medio."""
    page = get(home).decode("utf-8", "ignore")
    m = re.search(r'<link[^>]+type="application/(?:rss|atom)\+xml"[^>]*href="([^"]+)"', page, re.I) \
        or re.search(r'<link[^>]+href="([^"]+)"[^>]*type="application/(?:rss|atom)\+xml"', page, re.I)
    return urllib.parse.urljoin(home, m.group(1)) if m else None

def strip(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def clip(s, n=300):
    if len(s) <= n: return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"

def local(tag): return tag.rsplit("}", 1)[-1]

def parse(data):
    root = ET.fromstring(data)
    out = []
    for it in root.iter():
        if local(it.tag) not in ("item", "entry"): continue
        f = {"title":"","link":"","summary":"","date":None,"image":None}
        body = ""
        for c in it:
            t = local(c.tag)
            if t == "title": f["title"] = strip(c.text)
            elif t == "link": f["link"] = (c.get("href") or c.text or "").strip() or f["link"]
            elif t in ("description","summary"): f["summary"] = c.text or ""
            elif t == "encoded" or (t == "content" and not c.get("url")): body = c.text or ""
            elif t in ("pubDate","published","updated","date") and not f["date"]:
                try: f["date"] = parsedate_to_datetime(c.text.strip())
                except Exception:
                    try: f["date"] = datetime.fromisoformat(c.text.strip().replace("Z","+00:00"))
                    except Exception: pass
            elif t in ("content","thumbnail","enclosure") and c.get("url") and not f["image"]:
                if t != "enclosure" or (c.get("type") or "").startswith("image"): f["image"] = c.get("url")
        if not f["image"]:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)', body + f["summary"])
            if m: f["image"] = html.unescape(m.group(1))
        f["summary"] = clip(strip(f["summary"]))
        if f["title"] and f["link"].startswith("http"): out.append(f)
    return out

def run():
    items, status = [], []
    for s in SOURCES:
        got, err, used = [], None, None
        urls = list(s["feeds"])
        for attempt in range(2):
            for u in urls:
                try:
                    got = parse(get(u)); used = u
                    if got: break
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
            if got or attempt: break
            try:
                d = discover(s["home"])
                urls = [d] if d else []
            except Exception as e:
                err = f"{type(e).__name__}: {e}"; urls = []
        got.sort(key=lambda x: x["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        for g in got[:PER_SOURCE]:
            d = g["date"]
            if d and d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            items.append({"source":s["id"],"title":g["title"],"link":g["link"],"summary":g["summary"],
                          "image":g["image"],"date":d.astimezone(timezone.utc).isoformat() if d else None})
        status.append({"id":s["id"],"name":s["name"],"group":s["group"],"home":s["home"],"catholic":bool(s.get("catholic")),
                       "ok":bool(got),"count":min(len(got),PER_SOURCE),"feed":used,"error":None if got else (err or "Sin noticias en el feed")})
        print(("OK  " if got else "FALLO"), s["name"], len(got), err or "")
    json.dump({"generated_at":datetime.now(timezone.utc).isoformat(),"sources":status,"items":items},
              open("news.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    run()
