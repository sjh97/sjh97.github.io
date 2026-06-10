# Jehyeon Shin — Academic Homepage

Source code for my personal academic website: **<https://sjh97.github.io>**

I am a Ph.D. student at the **Graduate School of Artificial Intelligence, POSTECH**
(advised by Prof. Junsuk Rho), working on **metamaterials, metasurfaces, nanophotonics,
and AI-driven inverse design**. The site hosts my publications, CV, news, and contact info.

---

## ✨ What makes this repo a little different

The whole site is **generated from a single CV master file** so I never edit the website by hand.
I maintain one Excel sheet (`information.xlsx`) on my cloud drive — the same file I already use to
produce my Word/PDF CV — and a small pipeline turns it into the website content automatically.

```
information.xlsx (cloud)          ┌─ _bibliography/papers.bib   → Publications
        │  rclone sync            ├─ _data/cv_sections.yml      → CV page
        ▼                         ├─ _news/*.md                 → News feed
   _pipeline/generate.py  ───────▶├─ _data/socials.yml          → Social links
        ▲                         └─ _pages/about.md            → Bio
   profile.yml (site-only info)
        │  git push → GitHub Actions
        ▼
   https://sjh97.github.io
```

**To update the site** (no hand-editing of HTML/Markdown):

```bash
cd _pipeline && ./update.sh
```

This syncs the latest data, regenerates the content, and pushes — GitHub Actions then
builds and deploys automatically. See [`_pipeline/README.md`](_pipeline/README.md) for details.

## 🗂 Repository layout

| Path | Purpose |
|------|---------|
| `_pages/`, `_bibliography/`, `_data/`, `_news/` | Site content (mostly auto-generated) |
| `_pipeline/` | Automation: `update.sh`, `generate.py`, `profile.yml` |
| `_config.yml` | Site configuration |
| `assets/` | Images, PDF CV, styles |

## 🛠 Built with

This website is based on the **[al-folio](https://github.com/alshedivat/al-folio)** Jekyll theme
by Maruan Alshedivat and contributors — a clean, responsive theme for academics. Many thanks to
the al-folio community. The automated CV → site pipeline (`_pipeline/`) is my own addition.

## 📄 License

Site content (text, figures, CV) © Jehyeon Shin. The underlying al-folio theme is distributed
under the [MIT License](LICENSE).
