import streamlit as st
import pandas as pd
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Property Listing Parser")

SHEET_ID = "1JAShNVL2a1f8H8C487Pwni2IiBxr07euSEn3g0U2VV8"

# ✅ 选择客户 / tab
TAB_OPTIONS = ["te-lv", "elina", "self"]
selected_tab = st.selectbox("Select Client / Sheet", TAB_OPTIONS, index=0)

TAB_NAME = selected_tab

COLUMNS = [
    "Project", "Address", "Region", "Nearest MRT", "Price", "Size", "PSF",
    "Bedrooms", "Bathrooms", "Tenure", "TOP", "Developer", "Total Units",
    "URL", "Status", "Viewing Date", "Remarks"
]


# ---------- utils ----------
def clean_url(url):
    if not url:
        return ""
    m = re.search(r"(https://www\.propertyguru\.com\.sg/listing/for-sale-[a-z0-9\-]+-\d+)", url)
    return m.group(1) if m else url.split("?")[0]


def clean_text_line(s):
    return re.sub(r"\s+", " ", s).strip()


def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    try:
        book = client.open_by_key(SHEET_ID)
    except Exception as e:
        st.error(f"❌ Sheet连接失败: {e}")
        return None

    try:
        sheet = book.worksheet(TAB_NAME)
    except Exception as e:
        st.error(f"❌ 找不到 tab '{TAB_NAME}': {e}")
        return None

    return sheet


# ---------- save ----------
def save_to_gsheet(data):
    sheet = connect_sheet()
    if sheet is None:
        return

    values = sheet.get_all_values()

    if not values or not values[0] or values[0][0] != "Project":
        sheet.insert_row(COLUMNS, 1)

    url_col = COLUMNS.index("URL") + 1
    existing_urls = sheet.col_values(url_col)

    if data["URL"] in existing_urls:
        st.warning("⚠️ Duplicate URL - skipped")
        return

    row = [data.get(col, "") for col in COLUMNS]
    sheet.append_row(row)

    row_number = len(sheet.get_all_values())
    cell = gspread.utils.rowcol_to_a1(row_number, url_col)
    sheet.update_acell(cell, f'=HYPERLINK("{data["URL"]}", "Link")')


# ---------- parsing ----------
def find_first(text, patterns):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def extract_psf(text):
    vals = re.findall(r"S\$\s*([\d,]+(?:\.\d+)?)\s*psf", text, re.IGNORECASE)
    vals = [v.strip() for v in vals if v.strip()]
    if not vals:
        return ""

    decimal_vals = [v for v in vals if "." in v]
    if decimal_vals:
        return decimal_vals[-1]

    return vals[-1]


def extract_project(lines, text):
    for i, l in enumerate(lines):
        if l.lower() == "condos" and i + 2 < len(lines):
            return clean_text_line(lines[i + 2])

    m = re.search(
        r"^(.+?),\s*\d+[A-Za-z\-\/]?\s+[A-Za-z0-9'&\-\s]+,\s*\d+\s*Bedrooms?",
        text,
        re.IGNORECASE | re.MULTILINE
    )
    if m:
        return clean_text_line(m.group(1))

    return ""


def extract_developer(text):
    vals = re.findall(r"Developed by\s+(.+)", text, re.IGNORECASE)
    vals = [clean_text_line(v) for v in vals if clean_text_line(v)]
    if not vals:
        return ""
    return max(vals, key=len)


def clean_mrt(s):
    if not s:
        return ""

    m = re.search(
        r"(\d+(?:\.\d+)?\s*(?:m|km)\s*\(\d+\s*mins?\)\s*from\s+[A-Z0-9\/]+\s+[A-Za-z0-9\s\-/]+?MRT)",
        s,
        re.IGNORECASE
    )
    if m:
        return clean_text_line(m.group(1))

    m2 = re.search(
        r"([A-Z]{1,3}\d{1,2}(?:\/[A-Z]{1,3}\d{1,2})?\s+[A-Za-z0-9\s\-/]+?MRT)",
        s,
        re.IGNORECASE
    )
    if m2:
        return clean_text_line(m2.group(1))

    return clean_text_line(s)


def is_valid_mrt(s):
    if "mrt" not in s.lower():
        return False
    if not re.search(r"[A-Z]{1,3}\d{1,2}", s):
        return False
    return True


def extract_mrt(text):
    matches = re.findall(r"([^\n]*MRT)", text, re.IGNORECASE)
    candidates = []

    for m in matches:
        s = clean_mrt(m)
        if is_valid_mrt(s):
            candidates.append(s)

    if not candidates:
        return ""

    return max(candidates, key=len)


def extract_address(lines, text, project=""):
    bad_words = ["psf", "sqft", "mrt", "listing", "developer"]

    candidates = []

    patterns = [
        r"^\d+\s+Lorong\s+.+$",
        r"^\d+\s+Lengkong\s+.+$",
        r"^\d+\s+.+(?:Road|Drive|Walk|Lane|Close|Rise|Terrace)(?:\s+(?:West|East|North|South))?$",
        r"^\d+\s+[A-Za-z\s]{3,40}$"
    ]

    for l in lines:
        s = clean_text_line(l)
        if any(x in s.lower() for x in bad_words):
            continue
        for p in patterns:
            if re.match(p, s, re.IGNORECASE):
                candidates.append(s)

    if not candidates:
        return ""

    return sorted(candidates, key=len)[0]


def extract_region(lines):
    for i, l in enumerate(lines):
        if l.lower() == "condos" and i + 1 < len(lines):
            return clean_text_line(lines[i + 1])
    return ""


def extract(text):
    raw_url = find_first(text, [r"(https?://[^\s]+)"])
    url = clean_url(raw_url)

    lines = [clean_text_line(l) for l in text.splitlines() if clean_text_line(l)]
    project = extract_project(lines, text)

    return {
        "Project": project,
        "Address": extract_address(lines, text, project),
        "Region": extract_region(lines),
        "Nearest MRT": extract_mrt(text),
        "Price": find_first(text, [r"S\$\s*([\d,]+(?:\.\d+)?)"]),
        "Size": find_first(text, [r"([\d,]+)\s*sqft"]),
        "PSF": extract_psf(text),
        "Bedrooms": find_first(text, [r"Beds\s*(\d+)", r"(\d+)\s*Bedrooms?"]),
        "Bathrooms": find_first(text, [r"Baths\s*(\d+)"]),
        "Tenure": find_first(text, [r"(Freehold|99[- ]year lease|999[- ]year lease)"]),
        "TOP": find_first(text, [r"TOP.*?(\d{4})"]),
        "Developer": extract_developer(text),
        "Total Units": find_first(text, [r"(\d+)\s*total units"]),
        "URL": url,
        "Status": "New",
        "Viewing Date": "",
        "Remarks": ""
    }


# ---------- UI ----------
text = st.text_area("Paste listing text here", height=300)

col1, col2 = st.columns(2)

if "df" not in st.session_state:
    st.session_state.df = None

if col1.button("Extract"):
    d = extract(text)
    st.session_state.df = pd.DataFrame([[d.get(c, "") for c in COLUMNS]], columns=COLUMNS)

if st.session_state.df is not None:
    st.caption("✏️ You can edit before saving")

    st.session_state.df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed"
    )

if col2.button("Save"):
    if st.session_state.df is None:
        st.warning("Extract first")
    else:
        save_to_gsheet(st.session_state.df.iloc[0].to_dict())
        st.success(f"Saved to '{TAB_NAME}'")