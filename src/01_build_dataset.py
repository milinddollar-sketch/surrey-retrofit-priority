"""
Where Should Surrey Retrofit First?
Decision-support analysis at Surrey local-authority level.

Three OPEN government datasets (all Open Government Licence v3.0):
  1. ONS  - Energy efficiency of housing, LA districts (to FYE Mar 2022)
            -> % of dwellings below EPC band C (retrofit backlog, deduplicated stock)
            -> median energy efficiency score
            -> % of dwellings NOT on mains gas (harder / costlier to decarbonise)
  2. DESNZ - Sub-regional fuel poverty 2026 (2024 data), Table 2 (LA level)
            -> % of households in fuel poverty (LILEE)
  3. DESNZ - Sub-national gas consumption 2024
            -> median domestic gas consumption (kWh/meter) = heat demand proxy

Cross-check: MHCLG EB1 live table (existing dwellings by rating, to Q1 2026)
            -> current % of lodged existing-dwelling EPCs in bands D-G, per LA.

No arbitrary weighted "score", no ML. Transparent metrics, one decision chart.
Author: Milind Yadav
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = str(ROOT / "data")
OUT  = str(ROOT / "outputs")

SURREY = {
    "E07000207": "Elmbridge",
    "E07000208": "Epsom and Ewell",
    "E07000209": "Guildford",
    "E07000210": "Mole Valley",
    "E07000211": "Reigate and Banstead",
    "E07000212": "Runnymede",
    "E07000213": "Spelthorne",
    "E07000214": "Surrey Heath",
    "E07000215": "Tandridge",
    "E07000216": "Waverley",
    "E07000217": "Woking",
}
codes = list(SURREY)

# ---------- 1. ONS energy efficiency of housing (deduplicated stock) ----------
onf = f"{DATA}/ons_energy_efficiency_housing_LA_mar2022.xlsx"

def ons_table(sheet, valname):
    d = pd.read_excel(onf, sheet_name=sheet, header=3)
    d.columns = [str(c).strip() for c in d.columns]
    cc = [c for c in d.columns if "district code" in c.lower()][0]
    d = d[d[cc].isin(codes)][[cc, "All dwellings"]].copy()
    d.columns = ["code", valname]
    d[valname] = pd.to_numeric(d[valname], errors="coerce")
    return d

pc_c   = ons_table("1e", "pct_band_C_plus")     # % dwellings EPC C or above
score  = ons_table("1a", "median_epc_score")    # median SAP-style score

# heating fuel -> % not on mains gas
h = pd.read_excel(onf, sheet_name="5a", header=3)
h.columns = [str(c).strip() for c in h.columns]
hcc = [c for c in h.columns if "district code" in c.lower()][0]
h = h[h[hcc].isin(codes)][[hcc, "Mains gas"]].copy()
h.columns = ["code", "pct_mains_gas"]
h["pct_mains_gas"] = pd.to_numeric(h["pct_mains_gas"], errors="coerce")

# ---------- 2. DESNZ fuel poverty (2024) ----------
fp = pd.read_excel(f"{DATA}/desnz_fuel_poverty_sub_regional_2026.xlsx",
                   sheet_name="Table 2", header=None)
fp = fp[fp[0].isin(codes)][[0, 4, 5, 6]].copy()
fp.columns = ["code", "households", "fuel_poor_hh", "fuel_poverty_rate"]
for c in ["households", "fuel_poor_hh", "fuel_poverty_rate"]:
    fp[c] = pd.to_numeric(fp[c], errors="coerce")

# ---------- 3. DESNZ gas consumption (2024) ----------
g = pd.read_excel(f"{DATA}/desnz_subnational_gas_2024.xlsx", sheet_name="2024", header=5)
g.columns = [str(c).replace("\n", " ").strip() for c in g.columns]
gcc = g.columns[0]
med = [c for c in g.columns if "Median" in c and "Domestic" in c and "Non" not in c][0]
g = g[g[gcc].isin(codes)][[gcc, med]].copy()
g.columns = ["code", "median_gas_kwh"]
g["median_gas_kwh"] = pd.to_numeric(g["median_gas_kwh"], errors="coerce")

# ---------- 4. Cross-check: MHCLG EB1 current % D-G (existing dwellings) ----------
# EB1_by_LA is quarterly lodgement counts; take the latest 8 quarters (2 yrs) as a
# recent-flow snapshot to sanity-check the ONS stock ranking.
eb = pd.read_excel(f"{DATA}/mhclg_EB1_existing_dwellings_by_rating.ods",
                   engine="odf", sheet_name="EB1_by_LA", header=4)
eb.columns = [str(c).strip() for c in eb.columns]
codecol = eb.columns[0]; qcol = "Quarter"
bands = ["A","B","C","D","E","F","G"]
eb = eb[eb[codecol].isin(codes)].copy()
for b in bands + ["Not Recorded"]:
    eb[b] = pd.to_numeric(eb[b], errors="coerce")
recent_qs = ["2024/1","2024/2","2024/3","2024/4","2025/1","2025/2","2025/3","2025/4","2026/1"]
ebr = eb[eb[qcol].astype(str).isin(recent_qs)]
agg = ebr.groupby(codecol)[bands].sum()
agg["dg"] = agg[["D","E","F","G"]].sum(axis=1)
agg["tot"] = agg[bands].sum(axis=1)
agg["eb1_recent_pct_DG"] = 100 * agg["dg"] / agg["tot"]
eb_dg = agg["eb1_recent_pct_DG"].reset_index()
eb_dg.columns = ["code", "eb1_recent_pct_DG"]

# ---------- Merge ----------
df = pd.DataFrame({"code": codes})
df["local_authority"] = df["code"].map(SURREY)
for t in [pc_c, score, h, fp, g, eb_dg]:
    df = df.merge(t, on="code", how="left")

df["pct_band_D_G"]      = 100 - df["pct_band_C_plus"]     # retrofit backlog (stock)
df["pct_not_mains_gas"] = 100 - df["pct_mains_gas"]

df = df.sort_values("pct_band_D_G", ascending=False).reset_index(drop=True)

cols = ["local_authority","pct_band_D_G","fuel_poverty_rate","median_gas_kwh",
        "pct_not_mains_gas","median_epc_score","eb1_recent_pct_DG",
        "households","fuel_poor_hh","code"]
df[cols].to_csv(f"{OUT}/surrey_retrofit_master.csv", index=False)

pd.set_option("display.width", 160, "display.max_columns", 20)
print("SURREY RETROFIT MASTER TABLE (sorted by % homes below EPC C)\n")
show = df[["local_authority","pct_band_D_G","fuel_poverty_rate","median_gas_kwh",
           "pct_not_mains_gas","median_epc_score","eb1_recent_pct_DG"]].copy()
show.columns = ["Local authority","% below C (stock)","Fuel pov %","Med gas kWh",
                "% off gas","Med EPC score","% D-G (EPC 24-26)"]
print(show.round(1).to_string(index=False))

print("\nMedians (quadrant split lines):")
print(f"  % below EPC C : {df['pct_band_D_G'].median():.1f}")
print(f"  fuel poverty %: {df['fuel_poverty_rate'].median():.2f}")
print(f"  median gas kWh: {df['median_gas_kwh'].median():.0f}")

# correlation sanity check ONS stock vs EB1 recent flow
r = df["pct_band_D_G"].corr(df["eb1_recent_pct_DG"])
print(f"\nRank cross-check corr (ONS stock %DG vs EB1 recent %DG): r = {r:.2f}")
print("\nSaved -> outputs/surrey_retrofit_master.csv")
