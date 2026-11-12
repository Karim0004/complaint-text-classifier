from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "complaints.parquet"
LAST_DATE = "2017-02-28"

# channel and consent are left out because every narrative is a web complaint with consent (see notes.md)
COLUMNS = {
    "Complaint ID": "complaint_id",
    "Date received": "date_received",
    "Date sent to company": "date_sent",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Company": "company",
    "Tags": "tags",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response",
    "Consumer complaint narrative": "narrative",
    "Consumer disputed?": "disputed",
}

CATEGORY_COLUMNS = [
    "product", "sub_product", "issue", "sub_issue", "company",
    "tags", "company_response", "timely_response",
]


def clean_text(text):
    """Swap CFPB's redaction marks for one token each and tidy the whitespace."""
    # amounts are written as {$400.00}
    text = text.str.replace(r"\{\$[^}]*\}", " xxmoney ", regex=True)
    # redacted dates such as XX/XX/XXXX, XXXX/XXXX/15 and XXXX/2016
    text = text.str.replace(r"X{2,}(?:/[X\d]{2,4})+", " xxdate ", regex=True)
    # everything else that's redacted, with a run like XXXX XXXX XXXX counted once
    text = text.str.replace(r"X{2,}(?:\s+X{2,})*", " xxxx ", regex=True)
    return text.str.replace(r"\s+", " ", regex=True).str.strip()


def load_text(path=DATA_PATH):
    """Load the complaints that have a narrative and a dispute label, with the text cleaned."""
    df = pd.read_parquet(path, columns=list(COLUMNS)).rename(columns=COLUMNS)
    df = df[df["narrative"].notna()]

    # same label and cut-off as the complaint-escalation project (see notes.md)
    df = df[df["disputed"].isin(["Yes", "No"])].copy()
    df["disputed"] = (df["disputed"] == "Yes").astype(int)
    df = df[df["date_received"] <= LAST_DATE]

    for col in CATEGORY_COLUMNS:
        df[col] = df[col].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()

    # empty when the product has no sub-product or sub-issue, or the complaint has no tag
    for col in ["sub_product", "sub_issue", "tags"]:
        df[col] = df[col].fillna("None")

    df["company"] = df["company"].replace({"Riverwalk Financial CORPORATION": "Riverwalk Financial Corporation"})

    df["text"] = clean_text(df["narrative"])

    # how many complaints share the same text, to keep track of template letters
    df["copies"] = df.groupby(df["text"].str.lower())["text"].transform("size")

    return df.reset_index(drop=True)
