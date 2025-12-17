#!/usr/bin/env python3
import json
import os
from typing import List, Dict, Any

METADATA = "publications_metadata.json"
OUT_MD = "publications.md"
OUT_BIB = "biblio-confs-journals.bib"
BOLD_NAME = "Baris Kasikci"

MONTHS = {
    'Jan': 1, 'January': 1,
    'Feb': 2, 'February': 2,
    'Mar': 3, 'March': 3,
    'Apr': 4, 'April': 4,
    'May': 5,
    'Jun': 6, 'June': 6,
    'Jul': 7, 'July': 7,
    'Aug': 8, 'August': 8,
    'Sep': 9, 'September': 9,
    'Oct': 10, 'October': 10,
    'Nov': 11, 'November': 11,
    'Dec': 12, 'December': 12
}

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}")
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def month_to_num(m: str | None) -> int:
    return MONTHS.get(m or "", 0)

def fmt_authors_md(authors: List[str], bold_name: str = BOLD_NAME) -> str:
    out = []
    for a in authors:
        if a == bold_name:
            out.append(f"<b>{a}</b>")
        else:
            out.append(a)
    return ", ".join(out)

def fmt_authors_bibtex(authors: List[str]) -> str:
    return " and ".join(authors)

def escape_bibtex(text: str) -> str:
    """Escape LaTeX special characters for BibTeX fields."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "$": r"\$",
        "^": r"\^{}",
        "_": r"\_",
    }
    for ch, repl in replacements.items():
        text = text.replace(ch, repl)
    return text

def md_entry(pub: Dict[str, Any]) -> str:
    md = "1. "
    # title + url
    if pub.get("url"):
        md += f'[{pub["title"]}]({pub["url"]})'
    else:
        md += pub["title"]

    # code link
    if pub.get("code_url"):
        md += f' [<a href="{pub["code_url"]}">code</a>]'

    # video/slides
    if pub.get("video_url"):
        video_text = 'talk'
        md += f' [<a href="{pub["video_url"]}">{video_text}</a>'
        if pub.get("slides_url"):
            md += f',<a href="{{{{ site.baseurl }}}}{pub["slides_url"]}">slides</a>'
        md += ']'
    elif pub.get("slides_url"):
        md += f' [<a href="{{{{ site.baseurl }}}}{pub["slides_url"]}">slides</a>]'

    # authors
    md += ". "
    md += fmt_authors_md(pub["authors"]) + ". "

    # venue + abbr/link
    md += f'*{pub["venue"]}*'
    if pub.get("venue_url"):
        md += f' ([**{pub["venue_abbr"]}**]({pub["venue_url"]}))'
    else:
        md += f' ([**{pub["venue_abbr"]}**])'
    md += ". "

    # awards
    for award in pub.get("awards", []):
        if "IEEE Micro Top Pick" in award and "Honorable Mention" in award:
            md += "**IEEE Micro Top Pick Honorable Mention**. "
        elif "IEEE Micro Top Pick" in award:
            md += "**IEEE Micro Top Pick**. "
        elif award == "Best Paper Award":
            md += "**Best Paper Award** "
        elif award == "Best Student Paper Award":
            md += "**Best Student Paper Award**. "
        else:
            md += f"**{award}**. "

    # location (optional)
    if pub.get("location"):
        md += f'{pub["location"]}, '

    # date
    if pub.get("month"):
        md += f'{pub["month"]} {pub["year"]}'
    else:
        md += str(pub["year"])

    # award icon if any
    if pub.get("awards"):
        if not md.endswith("."):
            md += "."
        md += ' <img src="/~baris/public/award.png" style="width:15px;height:20px;">'

    return md

def bibtex_entry(pub: Dict[str, Any]) -> str:
    entry_type = "@article" if pub["type"] == "journal" else "@inproceedings"
    b = [f'{entry_type}{{{pub["bibtex_key"]},']
    b.append(f'  title     = {{{escape_bibtex(pub["title"])}}},')
    b.append(f'  author    = {{{fmt_authors_bibtex(pub["authors"])}}},')
    if pub["type"] == "journal":
        b.append(f'  journal   = {{{escape_bibtex(pub["venue"])}}},')
    else:
        # Prefer venue_abbr; fall back to venue
        book = pub.get("venue_abbr") or pub["venue"]
        b.append(f'  booktitle = {{{escape_bibtex(book)}}},')
    b.append(f'  year      = {{{pub["year"]}}},')
    if pub.get("month"):
        b.append(f'  month     = "{pub["month"]}"')
    else:
        b[-1] = b[-1].rstrip(",")
    b.append("}")
    return "\n".join(b)

def generate_publications_md(pubs: List[Dict[str, Any]]) -> str:
    md = "---\nlayout: page\ntitle: Publications\n---\n\n"

    def section(title: str, kind: str) -> str:
        part = f"### {title}\n<hr>\n\n"
        sel = [p for p in pubs if p["type"] == kind]
        sel.sort(key=lambda x: (-x["year"], -month_to_num(x.get("month"))))
        for p in sel:
            part += md_entry(p) + "\n\n"
        return part

    md += section("Conference Papers", "conference")

    journals = [p for p in pubs if p["type"] == "journal"]
    if journals:
        md += "### Journal Papers\n<hr>\n\n"
        journals.sort(key=lambda x: (-x["year"], -month_to_num(x.get("month"))))
        for p in journals:
            md += md_entry(p) + "\n\n"

    workshops = [p for p in pubs if p["type"] == "workshop"]
    md += "### Workshop Papers\n<hr>\n\n"
    workshops.sort(key=lambda x: (-x["year"], -month_to_num(x.get("month"))))
    for p in workshops:
        md += md_entry(p) + "\n"

    return md

def generate_bibtex(pubs: List[Dict[str, Any]]) -> str:
    selected = [p for p in pubs if p["type"] in ("conference", "journal")]
    selected.sort(key=lambda x: (-x["year"], -month_to_num(x.get("month"))))
    return "\n\n".join(bibtex_entry(p) for p in selected)

def main():
    data = load_json(METADATA)
    pubs = data.get("publications", [])
    md = generate_publications_md(pubs)
    bib = generate_bibtex(pubs)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(OUT_BIB, "w", encoding="utf-8") as f:
        f.write(bib)

    print("✓ Generated:", OUT_MD)
    print("✓ Generated:", OUT_BIB)
    print(f"Counts — conf: {sum(p['type']=='conference' for p in pubs)}, "
          f"journal: {sum(p['type']=='journal' for p in pubs)}, "
          f"workshop: {sum(p['type']=='workshop' for p in pubs)}")

if __name__ == "__main__":
    main()
