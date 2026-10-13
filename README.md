# LawCodex — Vatican City State (va)

Legislation of the **Stato della Città del Vaticano** (Vatican City State) — **catalogue only**.

Retrieved: **2026-10-13**. Source: *Stato e Governo › Legislazione e normativa* on the official
site of the Governatorato, https://www.vaticanstate.va/it/stato-e-governo/legislazione-e-normativa.html.

## Why there are no full texts here

Unlike most jurisdictions, Vatican City State expressly protects its legislation by copyright:

- **Legge N. CXCVII of 1 September 2017** (*Legge sulla protezione del diritto di autore sulle opere
  dell'ingegno e dei diritti connessi*), **art. 2**: «Le norme relative alla protezione e alla
  gestione del diritto di autore si applicano anche ai testi delle leggi e degli atti ufficiali
  pubblicati, in qualunque forma, dalla Santa Sede e dallo Stato della Città del Vaticano.»
  **Art. 5** vests the copyright in the Holy See / Vatican City State, and **art. 6** reserves the
  right to oppose any modification of the work.
- The vaticanstate.va site footer states «Copyright © 2026 by "Governatorato dello Stato della
  Città del Vaticano" | Tutti i diritti riservati».

In line with LawCodex rules (respect the source's terms; publish only what is permitted), the texts
are **not** republished. This repository instead contains a **catalogue** of every legislative
document published on the official site (number, date, title, type, status, page count and a
direct link to the official PDF). Publishing the texts would require authorisation from the
Governatorato (Segreteria Generale) / the Holy See's intellectual property commission
(art. 7 of the same law).

The scripts can still convert the texts locally for private use
(`python scripts/va_convert.py --texts /some/private/dir`).

## Coverage

**300 documents** catalogued in `catalogo/` (one file per category of the official site):

| File | Category on vaticanstate.va | Documents |
|---|---|---|
| `catalogo/legge-fondamentale.md` | Leggi fondamentali dello Stato | 3 |
| `catalogo/normativa-generale.md` | Normativa generale | 38 |
| `catalogo/normativa-penale-e-amministrativa.md` | Normativa in materia penale e amministrativa | 19 |
| `catalogo/persone-giuridiche.md` | Normativa persone giuridiche vaticane | 12 |
| `catalogo/prevenzione-finanziaria.md` | Prevenzione e contrasto in materia finanziaria / documenti sulla prevenzione delle attività illegali in campo finanziario | 24 |
| `catalogo/personale-governatorato.md` | Normativa sul personale del Governatorato | 7 |
| `catalogo/emergenza-sanitaria.md` | Normativa emergenza sanitaria | 10 |
| `catalogo/altre-materie.md` | Normativa altre materie | 9 |
| `catalogo/ordinanze-liste-sanzioni.md` | Ordinanze di aggiornamento della lista dei soggetti che minacciano la pace e la sicurezza internazionale | 178 |

By type: laws 43, decrees 42, ordinances 190, regulations 6, treaties/conventions 4, papal acts
(motu proprio / chirografi) 3, statute 1, fundamental laws 3, other 8.

The current constitution is the **Legge fondamentale dello Stato della Città del Vaticano of
31 July 2026** (Leo XIV), which «sostituisce integralmente» the Fundamental Law of 13 May 2023;
the 2023 and 2000 Fundamental Laws are listed with status `repealed`. Other documents have status
`unknown` (the site does not indicate which acts are still in force).

### Not covered

- Canon law of the Church and acts of the Holy See (Roman Curia) that are not Vatican City State
  legislation.
- Vatican City State legislation not posted on vaticanstate.va (the official publication is the
  *Supplemento per le leggi e disposizioni dello Stato della Città del Vaticano* of the *Acta
  Apostolicae Sedis*, not available as open data).

## Regenerate

```sh
pip install -r scripts/requirements.txt
python scripts/va_fetch.py      # parse category pages (with pagination) and download the PDFs into ../_raw/va/
python scripts/va_convert.py    # write catalogo/*.md  (add --texts DIR to also convert texts privately)
```

Text conversion uses poppler's `pdftotext`; scanned PDFs (51 of 300) are OCRed with `pdftoppm` +
`tesseract` (Italian model `ita.traineddata` from tesseract-ocr/tessdata_fast, expected in
`../_raw/va/tessdata/` or `$TESSDATA_DIR`).
