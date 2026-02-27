from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def plot_monthly_rain_ci(
    year_csv: Path,
    clim_mean_csv: Path,
    clim_std_csv: Path,
    out_plot: Path,
    title_year: int,
) -> Path:
    out_plot.parent.mkdir(parents=True, exist_ok=True)

    df_year = pd.read_csv(year_csv, parse_dates=["date"])
    clim_mean = pd.read_csv(clim_mean_csv)
    clim_std = pd.read_csv(clim_std_csv)

    df_year["month"] = df_year["date"].dt.month

    monthly_year = (
        df_year.groupby("month")["precip_mm"]
        .sum()
        .reset_index()
        .rename(columns={"precip_mm": "rain_year_mm"})
    )

    df_plot = (
        monthly_year
        .merge(clim_mean, on="month")
        .merge(clim_std, on="month")
    )

    df_plot["ci_lower"] = df_plot["monthly_mean_mm"] - 1.96 * df_plot["monthly_std_mm"]
    df_plot["ci_upper"] = df_plot["monthly_mean_mm"] + 1.96 * df_plot["monthly_std_mm"]
    df_plot["ci_lower"] = df_plot["ci_lower"].clip(lower=0)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8f8f8")

    months = df_plot["month"]

    ax.fill_between(
        months,
        df_plot["ci_lower"],
        df_plot["ci_upper"],
        color="gray",
        alpha=0.25,
        label="Baseline 95% CI"
    )

    ax.plot(
        months,
        df_plot["monthly_mean_mm"],
        linestyle="--",
        color="black",
        linewidth=1.5,
        label="Baseline Mean"
    )

    ax.bar(
        months,
        df_plot["rain_year_mm"],
        color="#3b6fa5",
        alpha=0.95,
        label=f"{title_year} Total"
    )

    ax.set_title(f"Monthly Rainfall vs Baseline ({title_year})")
    ax.set_xlabel("Month")
    ax.set_ylabel("Rainfall (mm)")
    ax.set_xticks(range(1, 13))
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(out_plot, dpi=160)
    plt.close()

    print("Saved:", out_plot)
    return out_plot

