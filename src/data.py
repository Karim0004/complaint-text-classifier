from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "complaints.parquet"
LAST_DATE = "2017-02-28"
LAST_TRAIN_DATE = "2016-09-30"

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


def build_parquet(csv_path, out_path=DATA_PATH):
    """Turn the downloaded CFPB CSV into the parquet file that load_text() reads.

    "N/A" is a real value in the dispute and consent columns, so only empty cells count as missing.
    The full CFPB file is several GB, so it's read in chunks and only 1 Jan 2015 to 24 Apr 2017 is kept.
    """
    chunks = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[""], chunksize=500_000)
    df = pd.concat(c[(c["Date received"] >= "2015-01-01") & (c["Date received"] <= "2017-04-24")] for c in chunks)
    for col in ["Date received", "Date sent to company"]:
        df[col] = pd.to_datetime(df[col])
    df["Complaint ID"] = df["Complaint ID"].astype(int)
    df.to_parquet(out_path, index=False)


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


def time_split(df, last_train_date=LAST_TRAIN_DATE):
    """Split by date received: train up to and including last_train_date, test after it."""
    train = df[df["date_received"] <= last_train_date]
    test = df[df["date_received"] > last_train_date]
    return train.reset_index(drop=True), test.reset_index(drop=True)
