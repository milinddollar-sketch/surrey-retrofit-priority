"""
Surrey retrofit priority quadrant.
X = % of homes below EPC band C (retrofit backlog, ONS stock to Mar 2022)
Y = % of households in fuel poverty (DESNZ 2024)
Bubble size = median domestic gas use, kWh/meter (DESNZ 2024) = heat-demand proxy
Runnymede highlighted.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

OUT = str(Path(__file__).resolve().parents[1] / "outputs")
df = pd.read_csv(f"{OUT}/surrey_retrofit_master.csv")

# ---- palette ----
INK   = "#16233b"   # near-navy text
GRID  = "#c9d2de"
BASE  = "#2f7d8c"   # teal bubbles
BASE_E= "#1c5563"
HL    = "#e07a2e"   # Runnymede amber
HL_E  = "#b95d17"
PRIOR = "#f6e2cf"   # priority quadrant wash
BG    = "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.edgecolor": INK,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
})

x = df["pct_band_D_G"].values
y = df["fuel_poverty_rate"].values
g = df["median_gas_kwh"].values
names = df["local_authority"].values
is_run = names == "Runnymede"

xm, ym = np.median(x), np.median(y)

# bubble sizes scaled from gas
smin, smax = 500, 3200
gs = (g - g.min()) / (g.max() - g.min())
sizes = smin + gs * (smax - smin)

fig, ax = plt.subplots(figsize=(13.2, 9.2), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

xpad = (x.max()-x.min())*0.16; ypad=(y.max()-y.min())*0.18
xlo, xhi = x.min()-xpad, x.max()+xpad
ylo, yhi = y.min()-ypad, y.max()+ypad
ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)

# priority quadrant wash (top-right: high backlog + high fuel poverty)
ax.axhspan(ym, yhi, xmin=(xm-xlo)/(xhi-xlo), xmax=1, color=PRIOR, zorder=0)

# median crosshair
ax.axvline(xm, color=GRID, ls=(0,(6,4)), lw=1.4, zorder=1)
ax.axhline(ym, color=GRID, ls=(0,(6,4)), lw=1.4, zorder=1)

# quadrant labels
ax.text(xhi-0.3, yhi-0.06, "RETROFIT FIRST\nhigh backlog · high fuel poverty",
        ha="right", va="top", fontsize=11, fontweight="bold", color=HL_E, zorder=2)
ax.text(xlo+0.3, yhi-0.06, "watch\nfuel poverty despite newer stock",
        ha="left", va="top", fontsize=9.5, color="#7c8698", zorder=2)
ax.text(xhi-0.3, ylo+0.10, "efficiency backlog\nbut lower fuel-poverty pressure",
        ha="right", va="bottom", fontsize=9.5, color="#7c8698", zorder=2)

# bubbles
for xi, yi, si, nm, run in zip(x, y, sizes, names, is_run):
    ax.scatter(xi, yi, s=si, color=HL if run else BASE,
               edgecolor=HL_E if run else BASE_E, linewidth=2.2 if run else 1.3,
               alpha=0.92 if run else 0.78, zorder=5 if run else 4)

# labels (offset to reduce overlap)
offsets = {
 "Mole Valley":(30,20),"Epsom and Ewell":(20,-26),"Tandridge":(-14,20),
 "Spelthorne":(-20,-22),"Guildford":(0,22),"Waverley":(-20,14),
 "Surrey Heath":(0,-26),"Elmbridge":(0,22),"Runnymede":(0,-32),
 "Woking":(4,18),"Reigate and Banstead":(0,-26),
}
for xi, yi, nm, run in zip(x, y, names, is_run):
    dx, dy = offsets.get(nm, (0,16))
    ax.annotate(nm, (xi, yi), textcoords="offset points", xytext=(dx,dy),
                ha="center", va="bottom" if dy>0 else "top",
                fontsize=11 if run else 10,
                fontweight="bold" if run else "normal",
                color=HL_E if run else INK, zorder=6)

# median tick annotations
ax.text(xm, ylo+0.02, f" Surrey median {xm:.0f}%", rotation=90, va="bottom",
        ha="right", fontsize=8.5, color="#9aa3b2")
ax.text(xlo+0.05, ym, f" median {ym:.1f}%", va="bottom", ha="left",
        fontsize=8.5, color="#9aa3b2")

ax.set_xlabel("Share of homes below EPC band C  (retrofit backlog, %)",
              fontsize=13, fontweight="bold", labelpad=10)
ax.set_ylabel("Households in fuel poverty  (%)",
              fontsize=13, fontweight="bold", labelpad=10)

for s in ["top","right"]:
    ax.spines[s].set_visible(False)
ax.tick_params(length=0)
ax.grid(axis="both", color="#eef1f5", lw=0.8, zorder=0)

# title block
fig.text(0.065, 0.965, "Where should Surrey retrofit first?",
         fontsize=23, fontweight="bold", color=INK, va="top")
fig.text(0.065, 0.917,
         "11 Surrey districts ranked on two independent signals of retrofit need. "
         "Bubble = median household gas use (heat demand).",
         fontsize=12.5, color="#5c6676", va="top")

# bubble-size legend
leg_g = [g.min(), np.median(g), g.max()]
leg_s = [smin + (gv-g.min())/(g.max()-g.min())*(smax-smin) for gv in leg_g]
lx = 0.845
handles = [Line2D([0],[0], marker='o', color='none', markerfacecolor=BASE,
                  markeredgecolor=BASE_E, markersize=np.sqrt(s)/1.6,
                  label=f"{gv/1000:.1f}k") for s,gv in zip(leg_s, leg_g)]
leg = ax.legend(handles=handles, title="Median gas\n(kWh/meter/yr)",
                loc="lower left", frameon=False, labelspacing=1.8,
                borderpad=1.1, handletextpad=1.4, fontsize=9.5,
                title_fontsize=9.5)
leg.get_title().set_color("#5c6676")

# Runnymede callout
ax.scatter([],[])
fig.text(0.065, 0.045,
    "Sources: ONS Energy efficiency of housing, LA districts (to Mar 2022) · DESNZ sub-regional fuel poverty 2026 (2024 data) · "
    "DESNZ sub-national gas consumption 2024. Open Government Licence v3.0.\n"
    "EPC backlog = ONS deduplicated dwelling stock below band C. Fuel poverty = LILEE. "
    "Bubble = median domestic gas per meter. Analysis: Milind Yadav, Jul 2026.",
    fontsize=8.3, color="#8a93a2", va="bottom")

plt.subplots_adjust(left=0.075, right=0.985, top=0.885, bottom=0.135)
fig.savefig(f"{OUT}/surrey_retrofit_quadrant.png", dpi=200, facecolor=BG)
print("saved outputs/surrey_retrofit_quadrant.png")
