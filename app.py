import streamlit as st
import pandas as pd
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Property Listing Parser")

COLUMNS = [
    "Project",
    "Address",
    "Area",
    "Nearest MRT",
    "Price",
    "Size",
    "PSF",
    "Bedrooms",
    "Bathrooms",
    "Tenure",
    "TOP",
    "Developer",
    "Total Units",
    "URL",
    "Status",
    "Viewing Date",
    "Remarks"
]


def clean_propertyguru_url(url):
    if not url:
        return ""

    m = re.search(
        r"(https://www\.propertyguru\.com\.sg/listing/for-sale-[a-z0-9\-]+-\d+)",
        url,
        re.IGNORECASE
    )
    if m:
        return m.group(1)

    # fallback: remove query string
    return url.split("?")[0].strip()


def save_to_gsheet(data):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key("11z6lns3BXO4hc_nabl_-9ugt_L9FdRMxGpBZ5lWJWS8").worksheet("te-lv")

    values = sheet.get_all_values()

    # 如果第一行不是 header，就自动补 header
    if not values or not values[0] or values[0][0] != "Project":
        sheet.insert_row(COLUMNS, 1)

    row = [data.get(col, "") for col in COLUMNS]
    sheet.append_row(row)

    # 让 URL 这一列变成可点击超链接
    url_col_index = COLUMNS.index("URL") + 1
    row_number = len(sheet.get_all_values())

    clean_url = data.get("URL", "")
    if clean_url:
        cell_label = gspread.utils.rowcol_to_a1(row_number, url_col_index)
        sheet.update_acell(cell_label, f'=HYPERLINK("{clean_url}", "{clean_url}")')


def slug_to_name(slug):
    parts = slug.replace("-", " ").split()
    return " ".join(word.capitalize() for word in parts)


def get_district(address, mrt, project, text):
    full_text = f"{address} {mrt} {project} {text}".lower()

    # 先直接抓句子里的 District xx
    m = re.search(r"\bin\s+district\s*(\d{1,2})\b", full_text, re.IGNORECASE)
    if m:
        return f"D{m.group(1)}"

    m = re.search(r"\bdistrict\s*(\d{1,2})\b", full_text, re.IGNORECASE)
    if m:
        return f"D{m.group(1)}"

    # 关键词映射
    address_map = {
        "D05": [
            "dover rise", "dover", "buona vista", "one-north", "one north",
            "west coast", "pasir panjang"
        ],
        "D15": [
            "east coast", "marine parade", "tanjong katong", "katong",
            "meyer", "amber", "siglap", "joo chiat", "still road"
        ],
        "D19": [
            "bartley", "serangoon", "hougang", "kovan", "upper paya lebar",
            "jalan bunga rampai", "poh huat"
        ],
        "D14": [
            "geylang", "eunos", "aljunied", "paya lebar", "kampong eunos"
        ],
        "D03": [
            "queenstown", "redhill", "tiong bahru", "alexandra",
            "bukit merah", "margaret"
        ],
        "D10": [
            "holland", "holland road", "bukit timah", "farrer",
            "leedon", "coronation", "sixth avenue"
        ]
    }

    mrt_map = {
        "D05": ["dover mrt", "buona vista mrt", "one-north mrt", "one north mrt"],
        "D15": ["marine parade mrt", "katong park mrt", "tanjong katong mrt"],
        "D19": ["bartley mrt", "serangoon mrt", "kovan mrt"],
        "D14": ["eunos mrt", "aljunied mrt", "paya lebar mrt"],
        "D03": ["queenstown mrt", "redhill mrt", "tiong bahru mrt"],
        "D10": ["holland village mrt", "farrer road mrt", "sixth avenue mrt"]
    }

    for district, keywords in address_map.items():
        if any(k in address.lower() for k in keywords):
            return district

    for district, keywords in mrt_map.items():
        if any(k in mrt.lower() for k in keywords):
            return district

    for district, keywords in address_map.items():
        if any(k in full_text for k in keywords):
            return district

    for district, keywords in mrt_map.items():
        if any(k in full_text for k in keywords):
            return district

    return ""


def extract(text):
    def find(patterns):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    raw_url = find([
        r"(https?://[^\s]+)"
    ])
    url = clean_propertyguru_url(raw_url)

    data = {
        "Project": "",
        "Address": "",
        "Area": "",
        "Nearest MRT": "",
        "Price": find([
            r"S\$\s*([\d,]+(?:\.\d+)?)"
        ]),
        "Size": find([
            r"([\d,]+)\s*sqft\s*floor\s*area",
            r"([\d,]+)\s*sqft"
        ]),
        "PSF": find([
            r"S\$\s*([\d,]+(?:\.\d+)?)\s*psf"
        ]),
        "Bedrooms": find([
            r"Beds\s*(\d+)",
            r"(\d+)\s*Beds?",
            r"(\d+)\s*bed"
        ]),
        "Bathrooms": find([
            r"Baths\s*(\d+)",
            r"(\d+)\s*Baths?",
            r"(\d+)\s*bath"
        ]),
        "Tenure": find([
            r"(999[- ]?year leasehold)",
            r"(999[- ]?year lease)",
            r"(99[- ]?year leasehold)",
            r"(99[- ]?year lease)",
            r"(Freehold(?: tenure)?)",
            r"(Leasehold)"
        ]),
        "TOP": find([
            r"TOP\s+in\s+[A-Za-z]+\s+(\d{4})",
            r"TOP.*?(\d{4})",
            r"Completed in\s+(\d{4})",
            r"Built.*?(\d{4})"
        ]),
        "Developer": find([
            r"Developed by\s+(.+)"
        ]),
        "Total Units": find([
            r"(\d+)\s*total units",
            r"comprises of\s+(\d+)\s+units"
        ]),
        "URL": url,
        "Status": "New",
        "Viewing Date": "",
        "Remarks": ""
    }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    junk = {
        "home-open-o", "furnished-o", "document-with-lines-o",
        "calendar-days-o", "calendar-time-o", "ruler-o", "auto-size-o",
        "people-behind-o", "layers-2-o", "new-project-o", "block-o",
        "property details", "condominium for sale", "unfurnished",
        "partially furnished", "fully furnished",
        "negotiable", "beds", "baths", "sqft", "psf",
        "not tenanted", "middle floor level", "low floor level",
        "high floor level", "starting from"
    }

    cleaned = [l for l in lines if l.lower() not in junk]

    # 先从 URL 抓 project
    if url:
        m = re.search(r"/for-sale-([a-z0-9\-]+)-\d+", url, re.IGNORECASE)
        if m:
            data["Project"] = slug_to_name(m.group(1))

    # 地址识别
    address_keywords = [
        "road", "rd", "street", "st", "avenue", "ave", "drive", "dr",
        "rise", "crescent", "lane", "close", "view", "hill", "grove",
        "place", "park", "boulevard", "way", "jalan", "lorong",
        "kampong", "eunos", "west"
    ]

    address = ""
    project_from_lines = ""

    for i, line in enumerate(cleaned):
        lower = line.lower()
        if (
            re.match(r"^(?:\d+[A-Za-z]?\s+.+|[A-Za-z][A-Za-z\s]+)$", line)
            and any(k in lower for k in address_keywords)
            and not any(x in lower for x in ["units", "psf", "sqft", "mrt", "lease", "developer"])
        ):
            address = line

            for j in range(i - 1, -1, -1):
                candidate = cleaned[j]
                c_lower = candidate.lower()

                if len(candidate) < 3:
                    continue
                if any(x in c_lower for x in [
                    "sale", "furnished", "lease", "listed", "developer",
                    "units", "psf", "sqft", "mrt", "floor", "tenanted"
                ]):
                    continue
                if not re.search(r"\d", candidate):
                    project_from_lines = candidate
                    break
            break

    data["Address"] = address

    if not data["Project"] and project_from_lines:
        data["Project"] = project_from_lines

    # MRT：只保留第一个，且清洗成纯站名
    mrt_matches = re.findall(
        r"(?:\d+\s*m\s*\(\d+\s*mins?\)\s*from\s*)?(?:[A-Z]{1,3}\d{1,2}\s+)?([A-Za-z][A-Za-z\s]+MRT)",
        text,
        re.IGNORECASE
    )

    cleaned_mrts = []
    for m in mrt_matches:
        name = re.sub(r"\s+", " ", m.strip())
        name = " ".join(word.capitalize() for word in name.split())
        if name not in cleaned_mrts:
            cleaned_mrts.append(name)

    if cleaned_mrts:
        data["Nearest MRT"] = cleaned_mrts[0]

    # 清理 tenure
    if data["Tenure"]:
        data["Tenure"] = data["Tenure"].replace(" tenure", "")

    # Area
    data["Area"] = get_district(
        data["Address"],
        data["Nearest MRT"],
        data["Project"],
        text
    )

    return data


text = st.text_area("Paste listing text here", height=320)

col1, col2 = st.columns(2)

if "df_result" not in st.session_state:
    st.session_state.df_result = None

if col1.button("Extract"):
    data = extract(text)
    ordered = {col: data.get(col, "") for col in COLUMNS}
    st.session_state.df_result = pd.DataFrame([ordered])[COLUMNS]

if st.session_state.df_result is not None:
    st.dataframe(st.session_state.df_result, use_container_width=True, hide_index=True)
    st.write("Preview (copy):")
    st.code(st.session_state.df_result.to_csv(sep="\t", index=False))

if col2.button("Save to Google Sheet"):
    if st.session_state.df_result is None:
        st.warning("Please Extract first")
    else:
        data = st.session_state.df_result.iloc[0].to_dict()
        try:
            save_to_gsheet(data)
            st.success("Saved to Google Sheet!")
        except Exception as e:
            st.error(f"GSheet save failed: {e}")