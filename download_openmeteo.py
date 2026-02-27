import requests
import pandas as pd
from pathlib import Path


def download_openmeteo(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    output_csv: Path,
    timezone: str,
) -> Path:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
            "shortwave_radiation_sum",
        ],
        "timezone": timezone,
    }

    print("Requesting data from Open-Meteo...")
    print(f"  lat/lon: {lat}, {lon}")
    print(f"  date range: {start_date} to {end_date}")
    print(f"  timezone: {timezone}")

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    df = pd.DataFrame(data["daily"])

    df.rename(
        columns={
            "time": "date",
            "temperature_2m_max": "tmax_C",
            "temperature_2m_min": "tmin_C",
            "precipitation_sum": "precip_mm",
            "relative_humidity_2m_max": "rh_max_pct",
            "relative_humidity_2m_min": "rh_min_pct",
            "shortwave_radiation_sum": "solar_MJ_m2",
        },
        inplace=True,
    )

    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(output_csv, index=False)

    print(f"Saved to {output_csv}")
    return output_csv

