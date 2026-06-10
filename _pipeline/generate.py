#!/usr/bin/env python3
"""
information.xlsx (CV 마스터 데이터) → al-folio 콘텐츠 자동 생성기.

생성물:
  _bibliography/papers.bib      (논문 — Publications 페이지)
  _data/cv_sections.yml         (CV 페이지: 학력/수상/장학금/학회/특허/강의/리뷰/언론)
  _data/socials.yml             (소셜 아이콘)
  _news/*.md                    (언론 보도 → 소식 피드)
  _pages/about.md               (자기소개 + 연구 관심사)

데이터 출처:
  - cache/information.xlsx       (OneDrive 에서 rclone 으로 동기화됨)
  - profile.yml                  (엑셀에 없는 사이트 전용 정보)

직접 실행:  uv run generate.py   (cache/information.xlsx 가 있어야 함)
보통은 update.sh 가 동기화 → 생성 → 커밋/푸시까지 처리합니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
XLSX = HERE / "cache" / "information.xlsx"
PROFILE = HERE / "profile.yml"

MONTHS = {m: i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"], start=0)}


# ----------------------------------------------------------------------------- helpers
def clean(v):
    """NaN / 빈 문자열 → None, 그 외엔 strip 된 값."""
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def as_int(v):
    v = clean(v)
    if v is None:
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return str(v)


def split_names(v):
    """쉼표로 구분된 저자/발명자 문자열 → 정리된 이름 리스트."""
    v = clean(v)
    if not v:
        return []
    return [n.strip().rstrip("*†").strip() for n in str(v).split(",") if n.strip()]


def fmt_ym(v):
    v = clean(v)
    if v is None:
        return None
    try:
        return pd.to_datetime(v).strftime("%Y.%m")
    except (ValueError, TypeError):
        return str(v)


def bib_escape(s: str) -> str:
    """BibTeX 자유 텍스트 필드용 최소 이스케이프 (URL/DOI 에는 쓰지 말 것)."""
    return (str(s).replace("\\", "")
            .replace("&", r"\&").replace("%", r"\%")
            .replace("#", r"\#").replace("_", r"\_"))


def load_profile() -> dict:
    with open(PROFILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sheets() -> dict[str, pd.DataFrame]:
    if not XLSX.exists():
        sys.exit(f"[오류] {XLSX} 가 없습니다. 먼저 update.sh 로 OneDrive 에서 동기화하세요.")
    xl = pd.ExcelFile(XLSX)
    return {s: xl.parse(s) for s in xl.sheet_names}


# ----------------------------------------------------------------------------- bib
def make_bib_key(authors, year, title, used):
    surname = "anon"
    if authors:
        surname = re.sub(r"[^A-Za-z]", "", authors[0].split()[-1]).lower() or "anon"
    word = ""
    for tok in re.findall(r"[A-Za-z]+", title or ""):
        if len(tok) > 2:
            word = tok.lower()
            break
    base = f"{surname}{year or ''}{word}"
    key = base
    i = 0
    while key in used:
        i += 1
        key = base + chr(ord("a") + i)
    used.add(key)
    return key


def build_bib(pub_df: pd.DataFrame, selected_dois: set[str]) -> str:
    used: set[str] = set()
    entries = []
    for _, row in pub_df.iterrows():
        title = clean(row.get("제목"))
        if not title:
            continue
        co_first = split_names(row.get("공동 1저자"))
        others = split_names(row.get("그외 저자"))
        corr = split_names(row.get("교신 저자"))
        authors = co_first + others + corr
        year = as_int(row.get("연도"))
        journal = clean(row.get("저널명"))
        volume = as_int(row.get("Volume"))
        pages = clean(row.get("페이지"))
        doi = clean(row.get("doi"))
        if doi:
            doi = str(doi).strip()
            doi = re.sub(r"(?i)^doi:\s*", "", doi)                       # "doi: 10.x" 접두 제거
            doi = re.sub(r"(?i)^\s*(https?://)?(dx\.)?doi\.org/", "", doi)  # "doi.org/10.x" 접두 제거
            doi = doi.strip().rstrip("/")
        impact = clean(row.get("IF"))

        if pages:
            pages = re.sub(r"^(\d+)\s*-\s*(\d+)$", r"\1--\2", str(pages))

        key = make_bib_key(authors, year, title, used)

        info = []
        if impact is not None and str(impact) not in ("-", "Pending", "0"):
            try:
                info.append(f"IF {float(impact):g}")
            except (TypeError, ValueError):
                pass
        if len(co_first) > 1:
            info.append("equal contribution among co-first authors")

        lines = [f"@article{{{key},"]
        lines.append("  bibtex_show = {true},")
        lines.append("  title       = {" + "{" + bib_escape(title) + "}" + "},")
        if authors:
            lines.append("  author      = {" + " and ".join(authors) + "},")
        if journal:
            lines.append("  journal     = {" + bib_escape(journal) + "},")
        if volume is not None:
            lines.append(f"  volume      = {{{volume}}},")
        if pages:
            lines.append(f"  pages       = {{{pages}}},")
        if year is not None:
            lines.append(f"  year        = {{{year}}},")
        if doi:
            lines.append(f"  doi         = {{{doi}}},")
            lines.append(f"  url         = {{https://doi.org/{doi}}},")
            lines.append(f"  html        = {{https://doi.org/{doi}}},")
        if info:
            lines.append("  additional_info = {<br><i>" + " · ".join(info) + "</i>},")
        if doi and doi in selected_dois:
            lines.append("  selected    = {true},")
        lines.append("}")
        entries.append("\n".join(lines))
    return "---\n---\n\n" + "\n\n".join(entries) + "\n"


# ----------------------------------------------------------------------------- cv sections
def sec(title, items, note=None):
    s = {"title": title, "items": items}
    if note:
        s["note"] = note
    return s


def build_cv_sections(data, profile) -> dict:
    sections = []

    # Education
    if "Education" in data:
        df = data["Education"].copy()
        df["_present"] = df["졸업연도"].isna()
        df = df.sort_values(by=["_present", "시작연도"], ascending=[False, False])
        items = []
        for _, r in df.iterrows():
            start = fmt_ym(r.get("시작연도")) or ""
            end = fmt_ym(r.get("졸업연도")) or "Present"
            degree = clean(r.get("학위")) or ""
            dept = clean(r.get("학과")) or ""
            inst = clean(r.get("소속")) or ""
            country = clean(r.get("국가"))
            advisor = clean(r.get("지도교수"))
            main = f"**{degree}** in {dept}, {inst}"
            if country:
                main += f" ({country})"
            item = {"date": f"{start} – {end}", "main": main}
            if advisor:
                item["sub"] = f"Advisor: {advisor}"
            items.append(item)
        sections.append(sec("Education", items))

    # Skills (profile.yml)
    skills = profile.get("skills") or []
    if skills:
        items = [{"main": f"**{s.get('category','')}** — {s.get('items','')}"} for s in skills]
        sections.append(sec("Skills", items))

    # Awards & Scholarship
    if "Award & Scholarship" in data:
        df = data["Award & Scholarship"].copy().sort_values(by="연도", ascending=False)
        awards, scholarships = [], []
        for _, r in df.iterrows():
            cls = clean(r.get("구분"))
            name = clean(r.get("수상명/장학금명")) or ""
            inst = clean(r.get("기관"))
            country = clean(r.get("국가"))
            year = as_int(r.get("연도"))
            end_year = as_int(r.get("연도끝"))
            amount = clean(r.get("장학금 금액"))
            tail = ", ".join(x for x in [inst, country] if x)
            main = f"**{name}**" + (f", {tail}" if tail else "")
            if cls == "장학금":
                date = f"{year} – {end_year}" if end_year else f"{year}"
                if amount:
                    main += f" ({amount})"
                scholarships.append({"date": date, "main": main})
            else:
                awards.append({"date": f"{year}", "main": main})
        if awards:
            sections.append(sec("Awards & Honors", awards))
        if scholarships:
            sections.append(sec("Scholarships", scholarships))

    # Conferences
    if "Conference" in data:
        df = data["Conference"].copy()
        df["_m"] = df["월"].map(lambda x: MONTHS.get(str(clean(x)), 0))
        df = df.sort_values(by=["연도", "_m"], ascending=[False, False])
        items = []
        for _, r in df.iterrows():
            name = clean(r.get("학회명")) or ""
            city = clean(r.get("도시"))
            country = clean(r.get("국가"))
            month = clean(r.get("월")) or ""
            year = as_int(r.get("연도"))
            loc = ", ".join(x for x in [city, country] if x)
            main = name + (f", {loc}" if loc else "")
            items.append({"date": f"{month} {year}".strip(), "main": main})
        sections.append(sec("Conference Presentations", items))

    # Patents
    if "Patent" in data:
        df = data["Patent"].copy().sort_values(by="출원(등록)일자", ascending=False)
        items = []
        for _, r in df.iterrows():
            invs = split_names(r.get("전체발명자명"))
            invs = ["**Jehyeon Shin**" if n == "Jehyeon Shin" else n for n in invs]
            title = clean(r.get("특허명")) or ""
            number = clean(r.get("출원(등록)번호")) or ""
            date = fmt_ym(r.get("출원(등록)일자")) or ""
            status = "Pending" if clean(r.get("출원/등록")) == "출원" else "Registered"
            loc = "Domestic" if clean(r.get("국내/국제")) == "Korea" else "International"
            numlabel = "Application No." if status == "Pending" else "Registration No."
            sub = f"{', '.join(invs)} · {numlabel} {number} · {loc}, {status}"
            items.append({"date": date, "main": title, "sub": sub})
        sections.append(sec("Patents", items))

    # Teaching
    if "TA" in data:
        df = data["TA"].copy().sort_values(by="학기", ascending=False)
        items = []
        for _, r in df.iterrows():
            sem = clean(r.get("학기")) or ""
            code = clean(r.get("학수번호")) or ""
            course = clean(r.get("교과목명")) or ""
            items.append({"date": str(sem),
                          "main": f"{course} ({code})",
                          "sub": "Teaching Assistant"})
        sections.append(sec("Teaching", items))

    # Peer Review
    if "Peer review" in data:
        df = data["Peer review"]
        counts: dict[str, int] = {}
        for _, r in df.iterrows():
            journal = clean(r.get("저널명"))
            status = clean(r.get("ORCID"))
            if not journal:
                continue
            counts.setdefault(journal, 0)
            if status and str(status).lower() == "verified":
                counts[journal] += 1
        items = []
        for journal, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            plural = "s" if n != 1 else ""
            items.append({"main": f"**{journal}** — {n} review{plural}"})
        if items:
            sections.append(sec("Professional Service", items,
                                note="Journal peer review (verified by ORCID)"))

    # Press & Broadcast
    press_groups = group_press(data)
    if press_groups:
        items = []
        for desc, outlets, maxdate in press_groups:
            links = ", ".join(f"[{name}]({url})" if url else name for name, url in outlets)
            items.append({"date": maxdate, "main": f'"{desc}"', "sub": links})
        sections.append(sec("Press & Broadcast", items))

    return {"sections": sections}


# ----------------------------------------------------------------------------- press / news
def group_press(data):
    """Press & Broadcast → [(대표설명, [(영문매체, url), ...], 'YYYY.MM'), ...] 최신순."""
    if "Press & Broadcast" not in data:
        return []
    df = data["Press & Broadcast"].copy()
    df = df.dropna(subset=["대표설명"])
    df["_d"] = pd.to_datetime(df["보도게재일자"], errors="coerce")
    groups: dict[str, dict] = {}
    for _, r in df.iterrows():
        key = clean(r.get("대표설명"))
        if not key:
            continue
        outlet = clean(r.get("보도 및 게재처 (영문)")) or clean(r.get("보도 및 게재처")) or ""
        url = clean(r.get("URL"))
        d = r.get("_d")
        g = groups.setdefault(key, {"outlets": {}, "dates": []})
        if outlet:
            g["outlets"][outlet] = url  # 중복 매체는 마지막 URL 유지
        if pd.notna(d):
            g["dates"].append(d)
    out = []
    for desc, g in groups.items():
        maxd = max(g["dates"]) if g["dates"] else None
        out.append((desc, sorted(g["outlets"].items()),
                    maxd.strftime("%Y.%m") if maxd is not None else "",
                    maxd))
    out.sort(key=lambda x: (x[3] is not None, x[3]), reverse=True)
    return [(d, o, m) for d, o, m, _ in out]


def slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "item"


def write_news(data):
    news_dir = REPO / "_news"
    # 파이프라인이 생성한 기존 소식 제거 (press- 접두)
    for f in news_dir.glob("press-*.md"):
        f.unlink()
    df = data.get("Press & Broadcast")
    if df is None:
        return 0
    dff = df.copy().dropna(subset=["대표설명"])
    dff["_d"] = pd.to_datetime(dff["보도게재일자"], errors="coerce")
    groups: dict[str, dict] = {}
    for _, r in dff.iterrows():
        key = clean(r.get("대표설명"))
        if not key:
            continue
        outlet = clean(r.get("보도 및 게재처 (영문)")) or ""
        url = clean(r.get("URL"))
        d = r.get("_d")
        g = groups.setdefault(key, {"outlets": {}, "dates": []})
        if outlet:
            g["outlets"][outlet] = url
        if pd.notna(d):
            g["dates"].append(d)
    n = 0
    for desc, g in groups.items():
        maxd = max(g["dates"]) if g["dates"] else None
        if maxd is None:
            continue
        date_str = maxd.strftime("%Y-%m-%d")
        links = ", ".join(f"[{name}]({url})" if url else name
                          for name, url in sorted(g["outlets"].items()))
        short = (desc[:70] + "…") if len(desc) > 70 else desc
        fname = news_dir / f"press-{maxd.strftime('%Y%m%d')}-{slugify(desc)}.md"
        body = (f"---\n"
                f"layout: post\n"
                f'title: \'Press coverage: "{short}"\'\n'
                f"date: {date_str}\n"
                f"inline: false\n"
                f"related_posts: false\n"
                f"---\n\n"
                f"Our work *{desc}* was featured in {links}.\n")
        fname.write_text(body, encoding="utf-8")
        n += 1
    return n


# ----------------------------------------------------------------------------- socials / about
def write_socials(profile):
    s = profile.get("socials") or {}
    allowed = ["email", "scholar_userid", "orcid_id",
               "github_username", "linkedin_username", "researchgate"]
    lines = ["# 자동 생성 파일 — _pipeline/profile.yml 의 socials 를 수정하세요.",
             "cv_pdf: /assets/pdf/cv.pdf",
             "rss_icon: false"]
    for k in allowed:
        v = clean(s.get(k))
        if v is not None:
            lines.append(f"{k}: {v}")
    (REPO / "_data" / "socials.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_about(profile):
    photo = profile.get("photo", "prof_pic.jpg")
    subtitle = " ".join(str(profile.get("subtitle", "")).split())
    affiliation = profile.get("affiliation", "")
    email = profile.get("email", "")
    bio = str(profile.get("bio", "")).rstrip()
    interests = profile.get("research_interests") or []

    more_info = f"<p>{affiliation}</p>"
    if email:
        more_info += f'\n    <p><a href="mailto:{email}">{email}</a></p>'

    fm = f"""---
layout: about
title: about
permalink: /
subtitle: >
  {subtitle}

profile:
  align: right
  image: {photo}
  image_circular: false
  more_info: >
    {more_info}

selected_papers: true
social: true

announcements:
  enabled: true
  scrollable: true
  limit: 5

latest_posts:
  enabled: false
---

"""
    body = bio + "\n"
    if interests:
        body += "\n**Research interests:** " + " · ".join(interests) + "\n"
    (REPO / "_pages" / "about.md").write_text(fm + body, encoding="utf-8")


# ----------------------------------------------------------------------------- main
def main():
    profile = load_profile()
    data = load_sheets()
    selected = {str(d).strip() for d in (profile.get("selected_dois") or [])}

    # 1) Publications → bib
    if "Publication" in data:
        bib = build_bib(data["Publication"], selected)
        (REPO / "_bibliography" / "papers.bib").write_text(bib, encoding="utf-8")
        npub = bib.count("@article")
    else:
        npub = 0

    # 2) CV sections
    cv = build_cv_sections(data, profile)
    with open(REPO / "_data" / "cv_sections.yml", "w", encoding="utf-8") as f:
        f.write("# 자동 생성 파일 — information.xlsx / profile.yml 를 수정하세요.\n")
        yaml.safe_dump(cv, f, allow_unicode=True, sort_keys=False, width=1000)

    # 3) News (press)
    nnews = write_news(data)

    # 4) socials + about
    write_socials(profile)
    write_about(profile)

    nsec = len(cv["sections"])
    print("✅ 생성 완료")
    print(f"   - papers.bib       : {npub} publications")
    print(f"   - cv_sections.yml  : {nsec} sections")
    print(f"   - _news            : {nnews} press items")
    print(f"   - socials.yml, about.md")


if __name__ == "__main__":
    main()
