# PMCC Website

This repository hosts the Hugo-based website for the **PM Connect Conference** organized by PMI Poland Chapter. The site is generated using the [Hugo static site generator](https://gohugo.io/) with a customized theme.

---

## 🚀 About the Project

The PMCC website is built to support:
- Multiedition content (`/2024`, `/2025`, etc.)
- Static fallback for past editions
- A responsive layout with soft/hard tracks, speaker bios, and conference agenda
- ...

---

## ⚙️ Tech Stack

- **Hugo** (v0.134.2+ recommended)
- **TOML** configuration
- **Navigator** Hugo theme (heavly customized)
- GitHub Pages or custom hosting ready

---

## 📁 Project Structure

```
pmcc/
├── config.toml               # Main configuration
├── content/                  # Markdown pages
│   ├── galeria/              # photo galery empty page
│   ├── regulamin/            # conf rules page 
│   ├── about_conf.md         # about conference content
│   └── call_for_papers.md    # call for papers process 
├── data/                     # (almost) each section has own yaml, if not it is config.toml
│   ├── agenda.yml
│   ├── bilety.yml
│   ├── call4papers.yml
│   ├── galeria.yml
│   ├── hero.yml
│   ├── opis_konfy.yml
│   ├── panel.yml
│   ├── partnerzy.yml
│   ├── prelegenci.yml
│   ├── speakers.yml
│   └── team.yml
├── layouts/                  # not used, all in theme 
├── public/                   # not git versioned, only simple update notification page  
├── resources/                # not used, all in theme   
├── static/                   # Static assets (CSS, JS, images)
├── themes/
│   └── navigator-hugo/       # Theme folder (customized)
└── README.md
```

---

## 🛠️ Setup and Local Development

### Prerequisites

- [Install Hugo](https://gohugo.io/getting-started/install/)
- Clone the repository:
  ```bash
  git clone https://github.com/PMI-Polska/pmcc.git
  cd pmcc
  ```
_Note: it is better to use git, and some IDE like VS code, but you can go the hard way._

### Run locally

```bash
hugo server -D
```

Visit `http://localhost:1313` in your browser.

---

## 🌍 Deployment Notes

TODO: updates needed here
- `baseURL` in `config.toml` should reflect the version if you want to archive previou edition (e.g., `https://pmcc.pmi.org.pl/2025`)
- Older editions (e.g., `2024`) are preserved as static exports for future-proofing

- To build static output:
  ```bash
  hugo --minify
  ```

---

## 🤝 Contributors

- **Maciej Koszykowski** – Lead Developer

---

## 📄 License

MIT License. See `LICENSE` file for details.

---

## 📬 Contact

Questions or suggestions? Contact us at [maciej.koszykowski@pmi.org.pl](mailto:maciej.koszykowski@pmi.org.pl)
