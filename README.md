# DecodeLabs — Project 1: Data Cleaning & Preparation

**Data Analytics Internship · Batch 2026 · DecodeLabs**

## Goal

Clean a raw e-commerce orders dataset by handling missing values, duplicate records, and inconsistent formatting (dates, numbers, text) — turning a messy raw source into a reliable, analysis-ready dataset.

## Files

| File | Description |
|---|---|
| `raw_orders.xlsx` | Original raw dataset (238 rows) — contains missing values, duplicate rows, duplicate Order_IDs, inconsistent city name spellings, mixed date formats, and inconsistent numeric precision |
| `cleaned_orders.xlsx` | Cleaned output (220 rows) — missing values imputed, duplicates removed, formats standardized |
| `clean_data.py` | Python (pandas) script that performs the full cleaning pipeline, reproducibly |
| `change_log.pdf` | Documentation of every change made — Change ID, description, impact, and status |

## Cleaning Process

**1. Missing Value Imputation**
- Numeric fields (`Qty`, `Value`) → filled with **median**
- Categorical fields (`City`, `Status`) → filled with **mode**
- Rows preserved rather than deleted, to avoid reducing statistical power

**2. Duplicate Removal**
- Exact full-row duplicates removed
- Remaining duplicate `Order_ID`s removed (first occurrence kept), enforcing Order_ID as a true unique key

**3. Format Standardization**
- City names collapsed to one canonical spelling per city (case, abbreviation, whitespace variants merged)
- `Status` trimmed and title-cased
- `Order_Date` converted to ISO 8601 (`YYYY-MM-DD`) from five mixed source formats
- `Value` rounded to 2 decimals, `Qty` cast to integer

## Verification (Project 2 Gate)

| Metric | Result |
|---|---|
| Duplicate Order_ID error rate | **0%** |
| Incorrectly formatted dates | **0%** |
| Remaining missing values | **0** |
| Raw → Cleaned rows | 238 → 220 (18 duplicates removed) |

## Tools Used

Python, pandas, openpyxl

---
*Maria — DecodeLabs Data Analytics Intern, 2026 Batch*
