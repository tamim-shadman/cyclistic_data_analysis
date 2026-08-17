"""Advanced spatial analysis utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import warnings
from typing import Optional

import folium
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster
from shapely.geometry import Point

matplotlib.use("Agg")

warnings.filterwarnings("ignore")


def perform_spatial_analysis(
    df_clean: Optional[pd.DataFrame], community_areas: Optional[gpd.GeoDataFrame] = None
) -> Optional[gpd.GeoDataFrame]:
    """Perform advanced spatial analysis with GeoJSON."""
    if df_clean is None:
        print("❌ No data available for spatial analysis")
        return None

    print("🗺️ Starting Advanced Spatial Analysis...")

    if not all(c in df_clean.columns for c in ["start_lat", "start_lng"]):
        print("  ⚠️ Coordinate columns not available for spatial analysis")
        return None

    df_spatial = df_clean.dropna(subset=["start_lat", "start_lng"]).copy()

    if len(df_spatial) == 0:
        print("  ⚠️ No valid coordinates for spatial analysis")
        return None

    geometry = [Point(xy) for xy in zip(df_spatial["start_lng"], df_spatial["start_lat"])]
    gdf_rides = gpd.GeoDataFrame(df_spatial, geometry=geometry, crs="EPSG:4326")

    try:
        gdf_rides_proj = gdf_rides.to_crs(epsg=3528)
    except Exception:
        gdf_rides_proj = gdf_rides

    print(f"✅ Created spatial dataframe with {len(gdf_rides):,} ride points")

    result = gdf_rides
    community_for_map = None
    community_col = None

    if community_areas is not None:
        print("\n1. 🏘️ COMMUNITY AREA ANALYSIS")
        try:
            ca = community_areas.copy()

            if ca.crs is None:
                ca.set_crs(epsg=4326, inplace=True)

            try:
                ca_proj = ca.to_crs(epsg=3528)
            except Exception:
                ca_proj = ca

            community_col = None
            for col in ["community", "community_name", "name", "area_name"]:
                if col in ca_proj.columns:
                    community_col = col
                    break

            if community_col is None:
                community_col = ca_proj.columns[0]
                print(f"  ⚠️ Using first available GeoJSON column as community column: {community_col}")

            if gdf_rides_proj.crs != ca_proj.crs:
                gdf_rides_proj = gdf_rides_proj.to_crs(ca_proj.crs)

            try:
                gdf_with_community = gpd.sjoin(gdf_rides_proj, ca_proj, how="left", predicate="within")
            except TypeError:
                gdf_with_community = gpd.sjoin(gdf_rides_proj, ca_proj, how="left", op="within")

            rides_by_community = gdf_with_community[community_col].value_counts().head(20)

            print("\nTop 20 Community Areas by Ride Count:")
            for i, (community, count) in enumerate(rides_by_community.items(), 1):
                print(f"  {i}. {community}: {count:,} rides")

            community_stats = gdf_with_community.groupby(community_col).size().reset_index(name="ride_count")
            community_areas_merged = ca_proj.merge(community_stats, on=community_col, how="left")
            community_areas_merged["ride_count"] = community_areas_merged["ride_count"].fillna(0)

            fig, ax = plt.subplots(figsize=(15, 12))
            community_areas_merged.plot(
                column="ride_count",
                cmap="YlOrRd",
                linewidth=0.8,
                ax=ax,
                edgecolor="0.8",
                legend=True,
                legend_kwds={"label": "Number of Rides", "orientation": "horizontal"},
                missing_kwds={"color": "lightgrey", "label": "No data"},
            )
            ax.set_title("Ride Density by Chicago Community Area", fontsize=18, fontweight="bold")
            ax.axis("off")
            plt.tight_layout()
            plt.savefig("eda_outputs/community_area_choropleth.png", dpi=300, bbox_inches="tight")
            plt.close()

            result = gdf_with_community

            community_for_map = community_areas_merged.to_crs(epsg=4326)[[community_col, "ride_count", "geometry"]].copy()
            community_for_map["__key__"] = community_for_map[community_col].astype(str)

        except Exception as e:
            print(f"  ⚠️ Community area analysis failed: {e}")

    # Interactive Folium map
    print("\n2. 🗺️ INTERACTIVE FOLIUM MAP")
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11)

    if community_for_map is not None:
        try:
            folium.Choropleth(
                geo_data=community_for_map.__geo_interface__,
                data=community_for_map,
                columns=["__key__", "ride_count"],
                key_on="feature.properties.__key__",
                fill_color="YlOrRd",
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name="Number of Rides",
            ).add_to(m)
        except Exception as e:
            print(f"  ⚠️ Could not add choropleth: {e}")

    sample_coords = df_spatial.sample(n=min(10000, len(df_spatial)), random_state=42)[["start_lat", "start_lng"]]
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in sample_coords.iterrows():
        folium.CircleMarker(
            location=[row["start_lat"], row["start_lng"]],
            radius=2,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6,
        ).add_to(marker_cluster)

    try:
        m.save("eda_outputs/interactive_chicago_rides.html")
        print("  💾 Saved interactive Folium map")
    except Exception as e:
        print(f"  ⚠️ Could not save Folium map: {e}")

    # Heatmap
    print("\n3. 🌡️ RIDE DENSITY HEATMAP")
    heat_df = df_clean.dropna(subset=["start_lat", "start_lng"]).sample(
        n=min(50000, len(df_clean)), random_state=42
    )
    heat_data = [[row["start_lat"], row["start_lng"]] for _, row in heat_df.iterrows()]

    if heat_data:
        heat_map = folium.Map(location=[41.8781, -87.6298], zoom_start=11)
        HeatMap(heat_data, radius=10, blur=15, max_zoom=13).add_to(heat_map)
        heat_map.save("eda_outputs/ride_density_heatmap.html")
        print("  💾 Saved ride density heatmap")
    else:
        print("  ⚠️ No valid coordinates for heatmap")

    # Station network analysis
    print("\n4. 🚉 STATION NETWORK ANALYSIS")
    if "start_station_name" in df_clean.columns and "end_station_name" in df_clean.columns:
        start_unique = df_clean["start_station_name"].nunique()
        end_unique = df_clean["end_station_name"].nunique()

        if start_unique <= 3000 and end_unique <= 3000:
            try:
                G = nx.DiGraph()

                ride_counts = (
                    df_clean.groupby(["start_station_name", "end_station_name"])
                    .size()
                    .reset_index(name="count")
                )

                for _, row in ride_counts.iterrows():
                    if (
                        pd.notna(row["start_station_name"])
                        and pd.notna(row["end_station_name"])
                        and row["start_station_name"] != "unknown"
                        and row["end_station_name"] != "unknown"
                    ):
                        G.add_edge(row["start_station_name"], row["end_station_name"], weight=row["count"])

                print(f"  Network nodes (stations): {G.number_of_nodes()}")
                print(f"  Network edges (routes): {G.number_of_edges()}")

                if G.number_of_nodes() > 0:
                    degree_centrality = nx.degree_centrality(G)
                    top_stations = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

                    print("\nTop 10 Most Connected Stations (Degree Centrality):")
                    for i, (station, centrality) in enumerate(top_stations, 1):
                        print(f"  {i}. {station}: {centrality:.4f}")

                    plt.figure(figsize=(15, 10))
                    pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
                    nx.draw_networkx_nodes(G, pos, node_size=50, node_color="skyblue", alpha=0.7)
                    nx.draw_networkx_edges(G, pos, alpha=0.1, arrows=True)
                    plt.title("Bike Station Network Visualization (Simplified)", fontsize=16, fontweight="bold")
                    plt.axis("off")
                    plt.tight_layout()
                    plt.savefig("eda_outputs/station_network.png", dpi=300, bbox_inches="tight")
                    plt.close()
                else:
                    print("  ⚠️ No usable station network could be built.")
            except Exception as e:
                print(f"  ⚠️ Station network analysis failed: {e}")
        else:
            print("  ⚠️ Too many unique station-like points for network analysis. Skipping to save memory.")
    else:
        print("  ⚠️ Station name columns not available for network analysis")

    return result