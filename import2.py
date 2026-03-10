import re
import time
import requests
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

ALPHA_VANTAGE_KEY = "e3dc984011a9c74a4c6dea35af93be09dcfbe3250f5ef7c3f9a805951d95f51b"

TICKER = "AAPL"
CIK = "0000320193"

LIMIT_FILINGS = 25

OUT_FILINGS = "aapl_filings_10q.csv"
OUT_IPHONE  = "aapl_iphone_net_sales.csv"
OUT_MERGED  = "aapl_q7_merged.csv"

SEC_HEADERS = {
    "User-Agent": "Tom Steinke tsteinke05@gmail.com (academic research)",
    "Accept-Encoding": "gzip, deflate",
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fetch_json(url):
    r = requests.get(url, headers=SEC_HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()

def fetch_html(url):
    r = requests.get(url, headers=SEC_HEADERS, timeout=60)
    r.raise_for_status()
    return r.text

def parse_money_to_float(value):

    if value is None:
        return None

    s = str(value)

    s = s.replace("$","")
    s = s.replace(",","")
    s = s.replace("(","-")
    s = s.replace(")","")

    try:
        return float(s)
    except:
        return None

# ============================================================
# STEP 1: GET FILINGS FROM SEC
# ============================================================

def get_aapl_10q_filings(limit=25):

    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"

    data = fetch_json(url)

    recent = data["filings"]["recent"]

    df = pd.DataFrame(recent)

    df = df[df["form"] == "10-Q"].copy()

    df["accessionNo"] = df["accessionNumber"]
    df["accessionNoNoDash"] = df["accessionNumber"].str.replace("-", "")

    cik_int = str(int(CIK))

    df["filingUrl"] = (
        "https://www.sec.gov/Archives/edgar/data/"
        + cik_int + "/"
        + df["accessionNoNoDash"] + "/"
        + df["primaryDocument"]
    )

    df["filedAt"] = pd.to_datetime(df["filingDate"])
    df["periodOfReport"] = pd.to_datetime(df["reportDate"])

    out = df[["filedAt","periodOfReport","accessionNo","filingUrl"]].head(limit)

    out.insert(0,"ticker",TICKER)
    out.insert(1,"companyName","Apple Inc.")
    out.insert(2,"formType","10-Q")

    return out


# ============================================================
# STEP 2: EXTRACT IPHONE SALES
# ============================================================

def extract_iphone_sales(filing_url):

    html = fetch_html(filing_url)

    try:
        tables = pd.read_html(html)
    except:
        return None

    for t in tables:

        text = " ".join(t.astype(str).values.flatten()).lower()

        if "iphone" not in text:
            continue

        mask = t.astype(str).apply(lambda c: c.str.contains("iphone",case=False))

        if not mask.any().any():
            continue

        row = t.loc[mask.any(axis=1)].iloc[0]

        for cell in row:

            val = parse_money_to_float(cell)

            if val:
                return val

    return None


def build_iphone_dataset(filings_df):

    rows = []

    for i,r in filings_df.iterrows():

        url = r["filingUrl"]

        print(f"Parsing {url}")

        try:
            sales = extract_iphone_sales(url)
        except:
            sales = None

        rows.append({
            "periodOfReport": r["periodOfReport"],
            "filedAt": r["filedAt"],
            "iphone_sales": sales
        })

        time.sleep(0.8)

    return pd.DataFrame(rows)


# ============================================================
# STEP 3: GET PRICES FROM ALPHA VANTAGE
# ============================================================

def get_prices():

    url = "https://www.alphavantage.co/query"

    params = {
        "function":"TIME_SERIES_DAILY",
        "symbol":TICKER,
        "outputsize":"full",
        "apikey":ALPHA_VANTAGE_KEY
    }

    r = requests.get(url,params=params)
    data = r.json()

    ts = data.get("Time Series (Daily)")

    if not ts:
        raise Exception(data)

    df = pd.DataFrame.from_dict(ts,orient="index")

    df.index = pd.to_datetime(df.index)

    df["close"] = pd.to_numeric(df["4. close"])

    return df[["close"]].sort_index()


# ============================================================
# STEP 4: COMPUTE RETURNS
# ============================================================

def compute_returns(iphone_df, prices):

    merged = iphone_df.copy()

    returns = []

    for _,r in merged.iterrows():

        date = r["filedAt"].date()

        try:

            start = prices.index.get_loc(pd.Timestamp(date),method="bfill")

            end = start + 21

            p0 = prices.iloc[start]["close"]
            p1 = prices.iloc[end]["close"]

            ret = (p1/p0) - 1

        except:
            ret = None

        returns.append(ret)

    merged["return_next_21_days"] = returns

    return merged


# ============================================================
# MAIN
# ============================================================

def main():

    filings = get_aapl_10q_filings(LIMIT_FILINGS)

    filings.to_csv(OUT_FILINGS,index=False)

    print("Saved filings")

    iphone = build_iphone_dataset(filings)

    iphone.to_csv(OUT_IPHONE,index=False)

    print("Saved iphone sales")

    prices = get_prices()

    merged = compute_returns(iphone,prices)

    merged.to_csv(OUT_MERGED,index=False)

    print("Saved merged dataset")

    print(merged.head())


if __name__ == "__main__":
    main()