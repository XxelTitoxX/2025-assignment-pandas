"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    root = Path(__file__).resolve().parent
    referendum_path = root / "data" / "referendum.csv"
    regions_path = root / "data" / "regions.csv"
    departments_path = root / "data" / "departments.csv"

    referendum = pd.read_csv(referendum_path, sep=";")
    regions = pd.read_csv(regions_path)
    departments = pd.read_csv(departments_path)

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """

    reg = regions.rename(columns={
        "code": "code_reg",
        "name": "name_reg"
    })
    dep = departments.rename(columns={
        "code": "code_dep",
        "name": "name_dep",
        "region_code": "code_reg"
    })

    # Harmonize department codes: strings, 2 chars (e.g. '01', '2A', '2B')
    dep["code_dep"] = dep["code_dep"].astype(str).str.zfill(2)

    reg = reg[["code_reg", "name_reg"]]
    dep = dep[["code_dep", "name_dep", "code_reg"]]

    merged = dep.merge(reg, on="code_reg", how="left")
    merged = merged[["code_reg", "name_reg", "code_dep", "name_dep"]]
    return merged


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """

    # Start from the original data, keep all original columns
    ref = referendum.copy()

    # Drop overseas / abroad departments containing 'Z' in their code
    ref = ref[~ref["Department code"].astype(str).str.contains("Z", na=False)]

    # Create a normalized department code to match departments.csv
    ref["code_dep"] = ref["Department code"].astype(str).str.zfill(2)

    # Ensure same format on the regions/departments side
    areas = regions_and_departments.copy()
    areas["code_dep"] = areas["code_dep"].astype(str).str.zfill(2)

    # Merge referendum with geographic info
    merged = ref.merge(areas, on="code_dep", how="left")

    # Tests require that there are no missing values
    merged = merged.dropna()

    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """

    df = referendum_and_areas.copy()

    vote_cols = ["Registered", "Abstentions", "Null", "Choice A", "Choice B"]
    # Make sure columns exist (defensive)
    for col in vote_cols:
        if col not in df.columns:
            df[col] = 0

    grouped = (
        df.groupby(["code_reg", "name_reg"], as_index=False)[vote_cols]
          .sum()
    )

    grouped = grouped.set_index("code_reg").sort_index()

    return grouped


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """

    root = Path(__file__).resolve().parent
    regions_geo_path = root / "data" / "regions.geojson"

    geo = gpd.read_file(regions_geo_path)

    geo = geo.rename(columns={
        "code": "code_reg",
        "nom": "name_reg",
        "name": "name_reg",
    })
    geo = geo[["code_reg", "name_reg", "geometry"]]

    df = referendum_result_by_regions.reset_index()
    # Drop name_reg from the stats to avoid name_reg_x/name_reg_y
    df = df.drop(columns=["name_reg"])

    merged = geo.merge(df, on="code_reg", how="left")

    expressed = merged["Choice A"].fillna(0) + merged["Choice B"].fillna(0)
    merged["ratio"] = merged["Choice A"].fillna(0) / expressed.replace(0, pd.NA)

    ax = merged.plot(
        column="ratio",
        cmap="RdBu",
        legend=True,
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )
    ax.set_axis_off()
    ax.set_title("Referendum - Choice A ratio by region")

    return merged


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
