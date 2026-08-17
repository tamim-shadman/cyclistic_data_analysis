"""User segmentation and clustering utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import warnings
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


def safe_mode(s: pd.Series):
    """Safely extract the mode value from a pandas Series."""
    mode_values = s.mode()
    return mode_values.iloc[0] if len(mode_values) > 0 else np.nan


def safe_top_category(s: pd.Series) -> str:
    """Safely extract the most frequent category from a pandas Series."""
    counts = s.value_counts(dropna=True)
    return counts.index[0] if len(counts) > 0 else "unknown"


def perform_user_segmentation(df_clean: pd.DataFrame) -> Optional[Dict]:
    """Perform clustering and segmentation analysis for bike-share users."""
    if df_clean is None:
        print("❌ No data available for user segmentation")
        return None

    print("👥 Starting Advanced User Segmentation...")

    if "member_type" not in df_clean.columns:
        print("❌ 'member_type' column not found - cannot perform user segmentation")
        return None

    user_metrics = None
    try:
        print("\n1. 🧑 USER DATA PREPARATION")
        grouped = df_clean.groupby("member_type", dropna=False)
        user_metrics = pd.DataFrame({
            "user_type": grouped.size().index.astype(str),
            "total_rides": grouped.size().values,
        })

        if "ride_duration" in df_clean.columns:
            duration_stats = grouped["ride_duration"].agg(["mean", "std", "min", "max"]).reset_index(drop=True)
            user_metrics = pd.concat([user_metrics, duration_stats], axis=1)

        if "distance_km" in df_clean.columns:
            distance_stats = grouped["distance_km"].agg(["mean", "std"]).reset_index(drop=True)
            distance_stats.columns = ["avg_distance", "std_distance"]
            user_metrics = pd.concat([user_metrics, distance_stats], axis=1)

        if "speed_kmh" in df_clean.columns:
            user_metrics["avg_speed"] = grouped["speed_kmh"].mean().values

        if "start_hour" in df_clean.columns:
            user_metrics["most_common_hour"] = grouped["start_hour"].agg(safe_mode).values

        if "is_weekend" in df_clean.columns:
            user_metrics["weekend_ratio"] = grouped["is_weekend"].mean().values

        if "ride_category" in df_clean.columns:
            user_metrics["most_common_category"] = grouped["ride_category"].agg(safe_top_category).values

        print(f"✅ Prepared user metrics with {len(user_metrics)} user types")
        if not user_metrics.empty:
            print(user_metrics.to_string(index=False))
    except Exception as exc:
        print(f"❌ Error preparing user metrics: {exc}")
        user_metrics = pd.DataFrame()

    cluster_analysis = None
    pca_df = None
    ride_clusters = None

    print("\n2. 🚲 RIDE-LEVEL CLUSTERING")
    cluster_features = [
        "ride_duration",
        "distance_km",
        "speed_kmh",
        "start_hour",
        "day_of_week",
        "is_weekend",
    ]
    available_features = [column for column in cluster_features if column in df_clean.columns]

    if len(available_features) > 1:
        df_sample = df_clean[available_features].dropna().copy()
        if len(df_sample) >= 100:
            sample_size = min(100000, len(df_sample))
            df_sample = df_sample.sample(n=sample_size, random_state=42).copy()

            scaler = StandardScaler()
            df_scaled = scaler.fit_transform(df_sample)

            print("  Finding optimal number of clusters...")
            max_k = min(8, len(df_scaled))
            ks = list(range(1, max_k + 1))
            distortions = []

            for k in ks:
                model = KMeans(n_clusters=k, random_state=42, n_init=10)
                model.fit(df_scaled)
                distortions.append(model.inertia_)

            plt.figure(figsize=(10, 6))
            plt.plot(ks, distortions, "bx-")
            plt.xlabel("Number of Clusters (k)", fontsize=14)
            plt.ylabel("Distortion", fontsize=14)
            plt.title("Elbow Method for Optimal k", fontsize=16, fontweight="bold")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("eda_outputs/elbow_curve.png", dpi=300, bbox_inches="tight")
            plt.close()

            optimal_k = 4
            if len(distortions) >= 3:
                second_diff = np.diff(distortions, 2)
                if len(second_diff) > 0:
                    optimal_k = ks[int(np.argmax(np.abs(second_diff))) + 1]

            optimal_k = max(2, min(optimal_k, len(df_scaled)))
            print(f"\nPerforming K-means clustering with k={optimal_k}...")

            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(df_scaled)
            df_sample["cluster"] = clusters
            cluster_analysis = df_sample.groupby("cluster").mean()

            print("\nCluster Analysis:")
            print(cluster_analysis.to_string())

            if "ride_duration" in available_features and "distance_km" in available_features:
                plt.figure(figsize=(12, 8))
                for cluster_id in range(optimal_k):
                    cluster_data = df_sample[df_sample["cluster"] == cluster_id]
                    plt.scatter(
                        cluster_data["ride_duration"],
                        cluster_data["distance_km"],
                        label=f"Cluster {cluster_id}",
                        alpha=0.6,
                        s=20,
                    )
                plt.xlabel("Ride Duration (minutes)", fontsize=14)
                plt.ylabel("Distance (km)", fontsize=14)
                plt.title("Ride Clustering: Duration vs Distance", fontsize=16, fontweight="bold")
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig("eda_outputs/ride_clusters.png", dpi=300, bbox_inches="tight")
                plt.close()

            print("\n3. 🔍 DBSCAN CLUSTERING FOR ANOMALY DETECTION")
            dbscan_sample = df_scaled[: min(20000, len(df_scaled))]
            dbscan = DBSCAN(eps=0.5, min_samples=10)
            dbscan_labels = dbscan.fit_predict(dbscan_sample)
            n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
            n_noise = list(dbscan_labels).count(-1)
            print(f"  Found {n_clusters} DBSCAN clusters and {n_noise} noise points (potential anomalies)")

            print("\n4. 📊 PRINCIPAL COMPONENT ANALYSIS (PCA)")
            pca = PCA(n_components=2)
            principal_components = pca.fit_transform(df_scaled)
            pca_df = pd.DataFrame(principal_components, columns=["PC1", "PC2"])
            pca_df["cluster"] = clusters

            plt.figure(figsize=(12, 8))
            for cluster_id in range(optimal_k):
                cluster_data = pca_df[pca_df["cluster"] == cluster_id]
                plt.scatter(
                    cluster_data["PC1"],
                    cluster_data["PC2"],
                    label=f"Cluster {cluster_id}",
                    alpha=0.6,
                    s=20,
                )
            plt.xlabel("Principal Component 1", fontsize=14)
            plt.ylabel("Principal Component 2", fontsize=14)
            plt.title("PCA Visualization of Ride Clusters", fontsize=16, fontweight="bold")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("eda_outputs/pca_clusters.png", dpi=300, bbox_inches="tight")
            plt.close()

            print(f"\nExplained variance ratio: {pca.explained_variance_ratio_}")
            print(f"Total explained variance: {sum(pca.explained_variance_ratio_):.2f}")
            ride_clusters = df_sample
        else:
            print("  ⚠️ Not enough complete rows for clustering.")
    else:
        print("  ⚠️ Not enough features available for clustering.")

    print("\n✅ User segmentation completed successfully!")
    return {
        "user_metrics": user_metrics,
        "ride_clusters": ride_clusters,
        "cluster_analysis": cluster_analysis,
        "pca_results": pca_df,
    }
