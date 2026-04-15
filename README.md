# Property Listing Parser (Streamlit)

A lightweight personal tool to parse PropertyGuru listings into structured data and save to Google Sheets.

## 🎯 Purpose

This tool is designed for **daily real estate workflow efficiency**, not for perfect parsing.

It helps:
- Reduce manual data entry
- Speed up listing tracking
- Minimize repetitive work (especially for ADHD / low-focus tasks)

---

## ⚡ Key Features

### 1. Paste → Extract → Save
- Paste PropertyGuru listing text
- Automatically extract structured fields
- Save to Google Sheet

### 2. Multi-tab support (client-based)
Select target sheet before saving:
- `te-lv`
- `elina`
- `self`

Each tab = one client / use case

---

### 3. Editable UI (critical)
After extraction:
- All fields are editable in-table
- Fix errors before saving

👉 This removes the need for perfect parsing

---

### 4. Smart parsing (heuristic-based)

#### Address
Supports common Singapore formats:
- `21 Lorong Lew Lian`
- `53 Lengkong Empat`
- `Poh Huat Road West`

#### MRT
- Extracts nearest MRT
- Automatically removes noise like `psf`

#### PSF
- Prefers precise values (e.g. `1,498.50` over `1,499`)

#### Developer
- Chooses the most complete version

---

### 5. Google Sheet integration
- Auto header creation
- URL de-duplication
- Clickable links
- Append-only workflow

---

## 🧠 Design Philosophy

This is a **heuristic, low-maintenance system**, not a perfect parser.

Key principles:

- 80% automation > 100% perfection
- Accept small manual fixes
- Optimize for speed and usability
- Avoid over-engineering

---

## 🔄 Workflow

1. Select client (tab)
2. Paste listing text
3. Click `Extract`
4. Edit fields if needed
5. Click `Save`

---

## ⚠️ Notes

- Google Sheet must already contain tabs:
  - `te-lv`
  - `elina`
  - `self`

- Some edge cases may not be parsed correctly  
  → Fix directly in the UI (by design)

---

## 🚀 Future Improvements (optional)

- Batch parsing
- Auto tagging (freehold / near MRT / school)
- Follow-up tracking (Next Action column)
- Simple CRM features

---

## 👤 shishi509

Personal productivity tool for real estate workflow optimization.