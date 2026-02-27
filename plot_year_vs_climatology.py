from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_year_vs_climatology(
    year_csv: Path,
    clim_mean_csv: Path,
    out_temp_plot: Path,
    title_year: int,
) -> Path:
    out_temp_plot.parent.mkdir(parents=True, exist_ok=True)

    df_2025 = pd.read_csv(year_csv, parse_dates=["date"])
    clim = pd.read_csv(clim_mean_csv)

    df_2025["doy"] = df_2025["date"].dt.dayofyear

    df_2025 = df_2025[~((df_2025["date"].dt.month == 2) & (df_2025["date"].dt.day == 29))]

    df = df_2025.merge(clim, on="doy", suffixes=("", "_clim"))

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8f8f8")

    ax.fill_between(
        df["date"],
        df["tmin_C_clim"],
        df["tmax_C_clim"],
        color="gray",
        alpha=0.25,
        label="Baseline Avg Range"
    )

    ax.plot(df["date"], df["tmax_C"], color="#d33f49", linewidth=2, label=f"{title_year} High")
    ax.plot(df["date"], df["tmin_C"], color="#2c7fb8", linewidth=2, label=f"{title_year} Low")

    ax.set_title(f"Temperature vs Baseline ({title_year})")
    ax.set_ylabel("Temperature (°C)")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(out_temp_plot, dpi=160)
    plt.close()

    print("Plot saved:")
    print("  ", out_temp_plot)

    return out_temp_plot

