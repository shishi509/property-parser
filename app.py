import streamlit as st
import pandas as pd
import re
import os

st.title("Property Listing Parser")


def slug_to_name(slug):
    parts = slug.replace("-", " ").split()
    return " ".join(word.capitalize() for word in parts)


def get_district(address, mrt, project, text):
    full_text = f"{address} {mrt} {project} {text}".lower()

    # 1) direct sentence extraction first
    m = re.search(r"\bin\s+district\s*(\d{1,2})\b", full_text, re.IGNORECASE)
    if m:
        return f"D{m.group(1)}"

    m = re.search(r"\bdistrict\s*(\d{1,2})\b", full_text, re.IGNORECASE)
    if m:
        return f"D{m.group(1)}"

    # 2) keyword mapping
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
            "jalan bunga rampai"
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

    url = find([
        r"(https?://[^\s]+)"
    ])

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
            r"(99[- ]?year leasehold)",
            r"(99[- ]?year lease)",
            r"(999[- ]?year leasehold)",
            r"(999[- ]?year lease)",
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
        "URL": url
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

    # project from URL first
    if url:
        m = re.search(r"/for-sale-([a-z0-9\-]+)-\d+", url, re.IGNORECASE)
        if m:
            data["Project"] = slug_to_name(m.group(1))

    # address detection
    address_keywords = [
        "road", "rd", "street", "st", "avenue", "ave", "drive", "dr",
        "rise", "crescent", "lane", "close", "view", "hill", "grove",
        "place", "park", "boulevard", "way", "jalan", "lorong", "kampong", "eunos"
    ]

    address = ""
    project_from_lines = ""

    for i, line in enumerate(cleaned):
        lower = line.lower()
        if (
            re.match(r"^\d+[A-Za-z]?\s+.+", line)
            and any(k in lower for k in address_keywords)
            and not any(x in lower for x in ["units", "psf", "sqft"])
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

    # MRT extraction: keep first nearest only, cleaned
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

    # clean tenure wording
    if data["Tenure"]:
        data["Tenure"] = data["Tenure"].replace(" tenure", "")

    # area mapping
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

    ordered = {
        "Project": data.get("Project", ""),
        "Address": data.get("Address", ""),
        "Area": data.get("Area", ""),
        "Nearest MRT": data.get("Nearest MRT", ""),
        "Price": data.get("Price", ""),
        "Size": data.get("Size", ""),
        "PSF": data.get("PSF", ""),
        "Bedrooms": data.get("Bedrooms", ""),
        "Bathrooms": data.get("Bathrooms", ""),
        "Tenure": data.get("Tenure", ""),
        "TOP": data.get("TOP", ""),
        "Developer": data.get("Developer", ""),
        "Total Units": data.get("Total Units", ""),
        "URL": data.get("URL", "")
    }

    st.session_state.df_result = pd.DataFrame([ordered])

if st.session_state.df_result is not None:
    st.dataframe(st.session_state.df_result, use_container_width=True, hide_index=True)
    st.write("Preview (copy):")
    st.code(st.session_state.df_result.to_csv(sep="\t", index=False))

if col2.button("Save to database"):
    if st.session_state.df_result is None:
        st.warning("Please Extract first")
    else:
        file = "property_records.csv"
        new_df = st.session_state.df_result

        if os.path.exists(file):
            old_df = pd.read_csv(file)

            new_url = str(new_df["URL"].iloc[0]).strip()
            if new_url and "URL" in old_df.columns and new_url in old_df["URL"].astype(str).values:
                st.warning("Duplicate found (same URL). Not saved.")
            else:
                updated_df = pd.concat([old_df, new_df], ignore_index=True)
                updated_df.to_csv(file, index=False)
                st.success("Saved successfully!")
        else:
            new_df.to_csv(file, index=False)
            st.success("Database created and saved!")