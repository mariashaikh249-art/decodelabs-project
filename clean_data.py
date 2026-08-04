import pandas as pd
import numpy as np

RAW_PATH = "/home/claude/project1/raw_orders.xlsx"
CLEAN_PATH = "/home/claude/project1/cleaned_orders.xlsx"

log = []  # (Change_ID, Description, Impact, Status)
n_id = 0
def add_log(desc, impact, status="Resolved"):
    global n_id
    n_id += 1
    log.append((f"CR{n_id:03d}", desc, impact, status))

df = pd.read_excel(RAW_PATH)
raw_rows = len(df)

# ============================================================
# PHASE 1: STRATEGIC IMPUTATION -- handle missing values (don't just delete)
# ============================================================

# Qty: numeric -> impute with MEDIAN
missing_qty = df["Qty"].isna().sum()
median_qty = df["Qty"].median()
df["Qty"] = df["Qty"].fillna(median_qty)
add_log(f"Imputed 'Qty' using Median ({median_qty})", f"Preserved {missing_qty} records")

# Value: numeric -> impute with MEDIAN (grouped by Product for accuracy where possible)
missing_value = df["Value"].isna().sum()
df["Value"] = df.groupby("Product")["Value"].transform(lambda s: s.fillna(s.median()))
# fallback for any product-group that was entirely NaN
overall_median_value = df["Value"].median()
df["Value"] = df["Value"].fillna(overall_median_value)
add_log("Imputed 'Value' using per-product Median", f"Preserved {missing_value} records")

# City: categorical -> impute with MODE
missing_city = df["City"].isna().sum()
mode_city = df["City"].mode(dropna=True)[0]
df["City"] = df["City"].fillna(mode_city)
add_log(f"Imputed 'City' using Mode ('{str(mode_city).strip()}')", f"Preserved {missing_city} records")

# Status: categorical -> impute with MODE
missing_status = df["Status"].isna().sum()
mode_status = df["Status"].mode(dropna=True)[0]
df["Status"] = df["Status"].fillna(mode_status)
add_log(f"Imputed 'Status' using Mode ('{mode_status.strip().title()}')", f"Preserved {missing_status} records")

# ============================================================
# PHASE 3 (applied before dedup so near-duplicates collapse cleanly):
# STANDARDIZE FORMATS -- text case/whitespace, city names, status, numeric precision
# ============================================================

# Product: trim + title-case consistently
df["Product"] = df["Product"].astype(str).str.strip().str.title()
# Fix known multi-word product casing edge cases (e.g. "Nexus-X" not "Nexus-X".title() issues)
df["Product"] = df["Product"].replace({"Nexus-X".title(): "Nexus-X"})

# City: map every messy variant to one canonical spelling
city_map = {
    "karachi": "Karachi", "khi": "Karachi",
    "lahore": "Lahore", "lhr": "Lahore",
    "islamabad": "Islamabad", "isb": "Islamabad",
    "faisalabad": "Faisalabad", "fsd": "Faisalabad",
    "multan": "Multan",
    "peshawar": "Peshawar", "pew": "Peshawar",
    "quetta": "Quetta",
}
city_changes = (df["City"].astype(str).str.strip().str.lower().map(city_map) != df["City"]).sum()
df["City"] = df["City"].astype(str).str.strip().str.lower().map(city_map)
add_log("Standardized 'City' to one canonical spelling per city", f"Corrected {city_changes} records")

# Status: trim + title case
status_changes = (df["Status"].astype(str).str.strip().str.title() != df["Status"]).sum()
df["Status"] = df["Status"].astype(str).str.strip().str.title()
add_log("Standardized 'Status' casing & whitespace", f"Corrected {status_changes} records")

# Order_Date: parse mixed formats -> ISO 8601 (YYYY-MM-DD)
def parse_date(s):
    return pd.to_datetime(s, dayfirst=False, errors="coerce")

parsed = pd.to_datetime(df["Order_Date"], errors="coerce", format="mixed", dayfirst=False)
# any that failed to parse, retry with dayfirst=True (covers DD/MM/YYYY ambiguity)
still_bad = parsed.isna()
if still_bad.any():
    retry = pd.to_datetime(df.loc[still_bad, "Order_Date"], errors="coerce", format="mixed", dayfirst=True)
    parsed.loc[still_bad] = retry

date_changes = (df["Order_Date"] != parsed.dt.strftime("%Y-%m-%d")).sum()
df["Order_Date"] = parsed.dt.strftime("%Y-%m-%d")
add_log("Converted 'Order_Date' to ISO 8601 (YYYY-MM-DD)", f"Corrected {date_changes} records")

# Numeric precision: Value -> 2 decimals, Qty -> integer
df["Value"] = df["Value"].round(2)
df["Qty"] = df["Qty"].astype(int)
add_log("Enforced numeric precision (Value: 2 decimals, Qty: integer)", f"Applied to all {len(df)} records")

# ============================================================
# PHASE 2: THE INTEGRITY AUDIT -- remove duplicates, unique IDs
# ============================================================

# 2a. Exact full-row duplicates
before = len(df)
df = df.drop_duplicates()
exact_dupes_removed = before - len(df)
add_log("Removed exact duplicate rows", f"Removed {exact_dupes_removed} records")

# 2b. Duplicate Order_ID (keep first occurrence -- Order_ID must be a unique key)
before = len(df)
df = df.sort_values("Order_ID").drop_duplicates(subset="Order_ID", keep="first")
id_dupes_removed = before - len(df)
add_log("Removed remaining duplicate Order_IDs (kept first record)", f"Removed {id_dupes_removed} records")

df = df.sort_values("Order_ID").reset_index(drop=True)

# ============================================================
# VERIFICATION GATE (Project 2 threshold)
# ============================================================
dup_id_rate = df["Order_ID"].duplicated().mean() * 100
bad_date_rate = pd.to_datetime(df["Order_Date"], format="%Y-%m-%d", errors="coerce").isna().mean() * 100
missing_any = df.isna().sum().sum()

verification = {
    "raw_rows": raw_rows,
    "clean_rows": len(df),
    "rows_removed_total": raw_rows - len(df),
    "duplicate_id_error_rate_pct": round(dup_id_rate, 4),
    "bad_date_format_rate_pct": round(bad_date_rate, 4),
    "remaining_missing_values": int(missing_any),
}

df.to_excel(CLEAN_PATH, index=False)

import json
with open("/home/claude/project1/verification.json", "w") as f:
    json.dump(verification, f, indent=2)

log_df = pd.DataFrame(log, columns=["Change ID", "Description", "Impact", "Status"])
log_df.to_csv("/home/claude/project1/change_log.csv", index=False)

print("=== VERIFICATION ===")
for k, v in verification.items():
    print(f"{k}: {v}")
print()
print(log_df.to_string(index=False))
