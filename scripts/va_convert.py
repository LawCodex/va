#!/usr/bin/env python3
"""Build the Vatican City State legislation catalogue from the documents cached by va_fetch.py.

By default only a *catalogue* (metadata + official links) is written into the repository,
because Vatican law (Legge N. CXCVII of 1 September 2017, art. 2 and 5) protects the texts of
laws and official acts by copyright, held by the Holy See / SCV. With `--texts DIR` the full
texts are also converted to Markdown into DIR (outside the repository, for private use).
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter

from pypdf import PdfReader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import va_textutil  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RAW = os.path.abspath(os.environ.get("VA_RAW", os.path.join(REPO, "..", "_raw", "va")))
RETRIEVED = os.environ.get("VA_RETRIEVED", datetime.date.today().isoformat())
MONTHS = {m: i + 1 for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                                          "agosto", "settembre", "ottobre", "novembre", "dicembre"])}
MONTHS["febbrario"] = 2
DIRS = {
    "leggi-fondamentali-dello-stato": "legge-fondamentale",
    "normativa-generale": "normativa-generale",
    "normativa-in-materia-penale-e-amministrativa": "normativa-penale-e-amministrativa",
    "normativa-persone-giuridiche-vaticane": "persone-giuridiche",
    "normativa-prevenzione-e-contrasto-in-materia-finanziaria-e-ft": "prevenzione-finanziaria",
    "documenti-sulla-prevenzione-delle-attivita-illegali-in-campo-finanziario": "prevenzione-finanziaria",
    "normativa-sul-personale-del-governatorato": "personale-governatorato",
    "normativa-emergenza-sanitaria": "emergenza-sanitaria",
    "normativa-altre-materie": "altre-materie",
    "ordinanze-aggiornamento-lista-soggetti-che-minacciano-la-pace-e-sicurezza-internazionale": "ordinanze-liste-sanzioni",
    "legislazione-e-normativa": "altre-materie",
}


def slugify(s, maxlen=80):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:maxlen].rstrip("-") or "documento"


def find_date(s):
    m = re.search(r"(\d{1,2})(?:°|º)?[\s.]+([A-Za-z]+)[\s.]+(\d{4})", s)
    if m and m.group(2).lower() in MONTHS:
        try:
            return datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
        except ValueError:
            return None
    m = re.search(r"\((\d{1,2})\.(\d{1,2})\.(\d{4})\)", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None


def roman_id(title):
    m = re.search(r"\bN\.?\s*([CDLXVIM]{1,12})\b", title)
    if m:
        return "N. " + m.group(1)
    m = re.search(r"\b(?:Legge|Decreto|Ordinanza)\s+(?:N\.?\s*)?([CDLXVIM]{1,12})\b", title)
    return ("N. " + m.group(1)) if m else None


def doc_type(cat, title):
    t = title.lower()
    if cat == "leggi-fondamentali-dello-stato":
        return "constitution"
    if "trattato" in t or "convenzione" in t or "accordo" in t:
        return "treaty"
    if "regolamento" in t[:60] or re.search(r"\breg\. di", t[:60]):
        return "regulation"
    if "ordinanza" in t or cat.startswith("ordinanze"):
        return "ordinance"
    if "decreto" in t[:80]:
        return "decree"
    if "legge" in t[:80]:
        return "act"
    if "motu proprio" in t or "chirografo" in t:
        return "papal_act"
    if "statuto" in t:
        return "statute"
    return "other"


def ocr_pages(pdf_path, key):
    """OCR a scanned PDF with pdftoppm + tesseract (Italian model); cached in _raw/va/ocr/."""
    cache = os.path.join(RAW, "ocr", key + ".json")
    if os.path.exists(cache):
        return json.load(open(cache))
    tess = os.environ.get("TESSDATA_DIR", os.path.join(RAW, "tessdata"))
    work = os.path.join(RAW, "ocr", key)
    os.makedirs(work, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", pdf_path, os.path.join(work, "p")], check=True)
    pages = []
    for img in sorted(os.listdir(work), key=lambda n: int(re.sub(r"\D", "", n) or 0)):
        r = subprocess.run(["tesseract", "--tessdata-dir", tess, os.path.join(work, img), "-", "-l", "ita"],
                           capture_output=True, text=True)
        pages.append(r.stdout)
    shutil.rmtree(work)
    json.dump(pages, open(cache, "w"))
    return pages


CAT_TITLES = {
    "legge-fondamentale": "Leggi fondamentali dello Stato",
    "normativa-generale": "Normativa generale",
    "normativa-penale-e-amministrativa": "Normativa in materia penale e amministrativa",
    "persone-giuridiche": "Normativa persone giuridiche vaticane",
    "prevenzione-finanziaria": "Normativa sulla prevenzione e il contrasto in materia finanziaria / attività illegali in campo finanziario",
    "personale-governatorato": "Normativa sul personale del Governatorato",
    "emergenza-sanitaria": "Normativa emergenza sanitaria",
    "altre-materie": "Normativa altre materie",
    "ordinanze-liste-sanzioni": "Ordinanze di aggiornamento della lista dei soggetti che minacciano la pace e la sicurezza internazionale",
}


def write_catalogue(catalogue):
    out = os.path.join(REPO, "catalogo")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for d, rows in sorted(catalogue.items()):
        rows.sort(key=lambda m: (m.get("date") or "", m["title"]), reverse=True)
        lines = ["---", f"title: {json.dumps(CAT_TITLES.get(d, d), ensure_ascii=False)}", "type: catalogue",
                 "jurisdiction: va", "language: it",
                 f"source: \"https://www.vaticanstate.va/it/stato-e-governo/legislazione-e-normativa.html\"",
                 f"retrieved: {RETRIEVED}", "---", "", f"# {CAT_TITLES.get(d, d)}", "",
                 "Catalogue only (metadata and official links) — see the repository README for why the texts "
                 "are not reproduced.", "",
                 "| Data | N. | Titolo | Tipo | Stato | Pagine | Documento ufficiale |", "|---|---|---|---|---|---|---|"]
        for m in rows:
            t = m["title"].replace("|", "\\|")
            lines.append(f"| {m.get('date', '')} | {m.get('identifier', '')} | {t} | {m['type']} | "
                         f"{m['status']} | {m['pages']} | [PDF]({m['source']}) |")
        open(os.path.join(out, d + ".md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    texts_dir = None
    if "--texts" in sys.argv:
        texts_dir = os.path.abspath(sys.argv[sys.argv.index("--texts") + 1])
    catalogue = {}
    items = json.load(open(os.path.join(RAW, "index.json")))
    out_root = texts_dir or os.path.join(RAW, "texts")
    for d in set(DIRS.values()):
        for root in (REPO, out_root):
            p = os.path.join(root, d)
            if os.path.isdir(p):
                shutil.rmtree(p)
    cats = {}
    for it in items:
        cats.setdefault(it["id"], []).append(it["category"])
    done, used = set(), set()
    stats, missing, scanned = Counter(), [], []
    newest_lf = None
    for it in items:
        if it["category"] == "leggi-fondamentali-dello-stato":
            d = find_date(it["title"])
            if d and (newest_lf is None or d > newest_lf):
                newest_lf = d
    for it in items:
        if it["id"] in done:
            continue
        done.add(it["id"])
        f = os.path.join(RAW, "pdf", it["id"] + ".bin")
        if not os.path.exists(f):
            missing.append(it["title"])
            continue
        data = open(f, "rb").read()
        if not data.startswith(b"%PDF"):
            missing.append(it["title"] + " (not a PDF)")
            continue
        try:
            r = subprocess.run(["pdftotext", "-enc", "UTF-8", f, "-"], capture_output=True) \
                if shutil.which("pdftotext") else None
            if r is not None and r.returncode == 0:
                pages = r.stdout.decode("utf-8", "replace").split("\f")
                if pages and not pages[-1].strip():
                    pages.pop()
            else:
                reader = PdfReader(f)
                pages = [p.extract_text() or "" for p in reader.pages]
        except Exception as e:  # noqa: BLE001
            missing.append(f"{it['title']} ({e})")
            continue
        ocr = False
        if sum(len(p.strip()) for p in pages) < 50 * max(1, len(pages)):
            pages = ocr_pages(f, it["id"])
            ocr = True
        body = va_textutil.to_markdown(pages)
        title = re.sub(r"\s+", " ", it["title"]).strip()
        typ = doc_type(it["category"], title)
        date = find_date(title)
        status = "unknown"
        if typ == "constitution":
            status = "in_force" if date == newest_lf else "repealed"
        meta = {"title": title}
        rid = roman_id(title)
        if rid:
            meta["identifier"] = rid
        meta["type"] = typ
        meta["jurisdiction"] = "va"
        meta["language"] = "it"
        if date:
            meta["date"] = date
        meta["status"] = status
        meta["categories"] = [DIRS.get(c, c) for c in dict.fromkeys(cats[it["id"]])]
        if ocr:
            meta["ocr"] = True
        meta["source"] = it["url"]
        meta["source_page"] = "https://www.vaticanstate.va/it/stato-e-governo/legislazione-e-normativa/" + it["category"] + ".html"
        meta["retrieved"] = RETRIEVED
        fm = ["---"]
        for k, v in meta.items():
            if isinstance(v, bool):
                fm.append(f"{k}: {'true' if v else 'false'}")
            elif k in ("type", "jurisdiction", "language", "status", "date", "retrieved"):
                fm.append(f"{k}: {v}")
            else:
                fm.append(f"{k}: " + json.dumps(v, ensure_ascii=False))
        fm.append("---")
        if not body.strip():
            scanned.append(title)
            body = ("*The official PDF contains no extractable text (scanned image); see the source link "
                    "for the document.*")
        text = "\n".join(fm) + f"\n\n# {title}\n\n{body}\n"
        d = DIRS.get(it["category"], "altre-materie")
        name = slugify(title, 90)
        if typ == "constitution":
            name = f"legge-fondamentale-{date}" if date else name
        base, k = name, 2
        while f"{d}/{name}" in used:
            name = f"{base}-{k}"
            k += 1
        used.add(f"{d}/{name}")
        catalogue.setdefault(d, []).append(meta | {"pages": len(pages)})
        fp = os.path.join(out_root, d, name + ".md")
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w", encoding="utf-8").write(text)
        stats[d] += 1
        stats["type:" + typ] += 1
    write_catalogue(catalogue)
    print(dict(stats), file=sys.stderr)
    print("missing", missing, file=sys.stderr)
    print("no text (scanned)", len(scanned), scanned, file=sys.stderr)


if __name__ == "__main__":
    main()
