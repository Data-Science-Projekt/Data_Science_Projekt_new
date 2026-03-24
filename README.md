# StockInsight Dashboard

An interactive Streamlit web application that systematically analyzes stock market behavior using real financial data and modern data science methods. Built as a Data Science project at Christian-Albrechts-Universität zu Kiel (CAU Kiel).

**Live App:** [stockinsight.streamlit.app](https://stockinsight.streamlit.app) *(Streamlit Community Cloud)*

---

## Introduction

Financial markets generate vast amounts of data daily — but which patterns are statistically meaningful, and which are just noise? StockInsight investigates this question through eight research questions, covering return distributions, volatility, risk metrics, sentiment, and fundamentals across six stocks from two sectors:

- **Tech:** Apple (AAPL), NVIDIA (NVDA), Microsoft (MSFT)
- **Finance:** JPMorgan (JPM), Goldman Sachs (GS), Bank of America (BAC)

### Research Questions

| # | Topic | Question |
|---|-------|----------|
| RQ1 | Return Analysis | Are the daily returns of Apple and NVIDIA normally distributed, or do they deviate significantly from the Gaussian assumption? |
| RQ2 | Volatility | How do the intraday trading ranges of tech stocks compare to those of financial stocks over time? |
| RQ3 | Technical Analysis | Do volume spike patterns differ systematically between the technology and financial sectors? |
| RQ4 | Market Phases | Can bull and bear market phases be systematically identified, and how do individual stocks behave across these regimes? |
| RQ5 | Market Structure | How do Apple and NVIDIA react to periods of elevated market stress as measured by the VIX index? |
| RQ6 | Risk Management | What are the Value-at-Risk and Expected Shortfall levels for Apple and NVIDIA, and how do their risk profiles compare? |
| RQ7 | Company Fundamentals | Does the quarterly iPhone sales volume statistically correlate with Apple's stock price returns in the month following earnings? |
| RQ8 | Sentiment Correlation | How does the Consumer Sentiment Index correlate with the monthly returns of tech and financial stocks? |

### Data Sources

| Source | Data | Update Frequency |
|--------|------|-----------------|
| [Alpha Vantage API](https://www.alphavantage.co/) | Daily OHLCV stock data (6 stocks) | Daily (automated) |
| [FRED API](https://fred.stlouisfed.org/) | S&P 500, VIX, Consumer Sentiment Index | Daily (automated) |
| Statista / IDC / Apple Earnings | Quarterly iPhone unit sales & earnings-day prices | Manual |

---

## Data Pipeline

The data pipeline runs fully automated via GitHub Actions and feeds the Streamlit app with up-to-date CSV files.

```
Alpha Vantage API ──┐
                    ├──> GitHub Actions (daily, 7 AM UTC)
FRED API ───────────┘         │
                              ▼
                        data_update.py
                              │
                              ▼
                        /data/*.csv
                     (stocks, VIX, sentiment)

Manual iPhone Data ──────> /data/iphone_sales.csv

                              │
                              ▼
                    Streamlit App (app.py)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        Analysis Pages   Info Pages     PDF/PNG Export
        (8 modules)      (home, about,  (utils/export.py)
                          team, etc.)
```

### How it works

1. **GitHub Actions** triggers `data_update.py` daily at 7:00 AM UTC (or manually via workflow dispatch).
2. `data_update.py` fetches the latest ~100 trading days from Alpha Vantage (stock OHLCV) and FRED (VIX, Consumer Sentiment, S&P 500) using API keys stored in GitHub Secrets.
3. Data is saved as CSV files in `/data/` and auto-committed to the repository.
4. The Streamlit app loads these local CSV files on startup — no live API calls are made during user interaction, ensuring fast and reliable page loads.
5. iPhone sales data (`iphone_sales.csv`) is maintained manually from Statista/IDC/Apple earnings reports.

---

## Application Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Streamlit (multipage app) |
| Data Processing | Pandas, NumPy |
| Statistical Analysis | SciPy (Pearson, Spearman, OLS regression, kurtosis, skewness) |
| Visualization | Plotly (interactive charts) |
| Export | pypdf, kaleido (PDF/PNG generation) |
| CI/CD | GitHub Actions (daily data updates) |
| Deployment | Streamlit Community Cloud |

### Project Structure

```
├── app.py                    # Entry point & navigation config — built with Claude Opus 4.6 & Gemini 3 Pro
├── data_update.py            # Automated data fetching script — built with Claude Opus 4.6 & Gemini 3 Pro
├── requirements.txt          # Python dependencies
│
├── analysis/                 # Analysis page modules
│   ├── return_analysis.py    # RQ1: Return distributions — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── range_analysis.py     # RQ2: Volatility comparison — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── technische_analyse.py # RQ3: Volume spike analysis — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── marktphasen.py        # RQ4: Bull/bear phase detection — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── marktstruktur.py      # RQ5: VIX stress testing — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── risikomanagement.py   # RQ6: VaR & Expected Shortfall — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── company_fundamentals.py # RQ7: iPhone sales vs. stock returns — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── sentiment_correlation.py # RQ8: Consumer sentiment vs. returns — built with Claude Opus 4.6 & Gemini 3 Pro
│   └── utils.py              # Shared helpers (page header, caching, API) — built with Claude Opus 4.6 & Gemini 3 Pro
│
├── pages/                    # Informational pages
│   ├── home.py               # Landing page with project overview — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── about_project.py      # Goals, methodology, dataset description — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── fazit.py              # Conclusion & key findings — built with Claude Opus 4.6 & Gemini 3 Pro
│   ├── team.py               # Team members — built with Claude Opus 4.6 & Gemini 3 Pro
│   └── imprint.py            # Legal information — built with Claude Opus 4.6 & Gemini 3 Pro
│
├── utils/
│   └── export.py             # PDF/PNG export utilities — built with Claude Opus 4.6 & Gemini 3 Pro
│
├── data/                     # Auto-updated CSV data files
│   ├── stock_AAPL.csv        # Daily OHLCV per stock
│   ├── stock_NVDA.csv
│   ├── stock_MSFT.csv
│   ├── stock_JPM.csv
│   ├── stock_GS.csv
│   ├── stock_BAC.csv
│   ├── macro_vix.csv         # CBOE Volatility Index
│   ├── consumer_sentiment.csv # U of Michigan Consumer Sentiment
│   └── iphone_sales.csv      # Quarterly iPhone sales & earnings data
│
└── .github/workflows/
    └── main.yml              # GitHub Actions: daily data update
```

### How the website was built

The app is built as a **Streamlit multipage application**. `app.py` defines the navigation structure with `st.Page()` and `st.navigation()`, grouping the eight analysis pages into thematic sections (Stock Behavior, Market Environment, Risk Analysis, Sentiment & Macro, Fundamentals).

Each analysis module:
1. Loads pre-fetched CSV data from `/data/` using `pd.read_csv()` with Streamlit's `@st.cache_data` for performance.
2. Performs statistical computations (distribution fitting, correlation, regression, VaR simulation, etc.) using SciPy and NumPy.
3. Renders interactive Plotly charts with hover tooltips, and provides sidebar controls for adjustable parameters (date ranges, confidence levels, thresholds).
4. Offers PDF/PNG export of charts via download buttons.

**Deployment:** The app is deployed on Streamlit Community Cloud, which auto-deploys from the GitHub repository. API keys for local development are stored in `.streamlit/secrets.toml` (gitignored).

---

## How to Use the Application

### Navigation

Use the **sidebar** (click the arrow in the top-left corner) to navigate between sections and pages. Each analysis page includes sidebar controls to adjust parameters.

### Analysis Pages — Highlights

**Return Analysis (RQ1)**
- View log-return distributions for Apple and NVIDIA with fitted Gaussian overlays.
- Compare kurtosis and skewness to detect fat tails — a key indicator that normal distribution assumptions fail.

**Volatility (RQ2)**
- Compare intraday trading ranges across tech vs. finance sectors.
- Toggle between absolute and relative range metrics.

**Technical Analysis (RQ3)**
- Explore volume spike detection using Z-score anomaly detection with a 20-day rolling window.
- Compare spike frequencies between sectors.

**Market Phases (RQ4)**
- Visualize bull, bear, and neutral market phases with color-coded shading on price charts.
- Analyze phase durations and transitions for all six stocks.

**Market Structure (RQ5)**
- Adjust the VIX panic threshold to define market stress scenarios.
- Compare how Apple and NVIDIA perform during high-volatility regimes.

**Risk Management (RQ6)**
- Set the confidence level (90–99%) and compare Value-at-Risk vs. Expected Shortfall.
- Observe how CVaR captures tail risk that VaR alone misses.

**Company Fundamentals (RQ7)**
- Explore the scatter plot of iPhone unit sales vs. 30-day post-earnings returns.
- View OLS regression results and Pearson correlation with p-values.

**Sentiment Correlation (RQ8)**
- Select individual stocks or sectors to analyze against the Consumer Sentiment Index.
- Compare Pearson and Spearman correlations for different aggregation periods.

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/Data-Science-Projekt/Data_Science_Projekt_new.git
cd Data_Science_Projekt_new

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## LLM Attribution

All code in this project was developed with the assistance of Claude Opus 4.6
and Gemini 3 Pro.

---

Christian-Albrechts-Universität zu Kiel — Data Science Project 2026
