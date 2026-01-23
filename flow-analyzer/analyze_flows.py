import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 8)


def load_flow_data(csv_path: str) -> pd.DataFrame:
    """Load CICFlowMeter CSV data."""
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} flows from {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise


def basic_statistics(df: pd.DataFrame, output_dir: Path) -> None:
    """Display basic flow statistics and save summary table."""
    logger.info("=== Basic Flow Statistics ===")
    logger.info(f"Total flows: {len(df)}")
    logger.info(f"Unique source IPs: {df['src_ip'].nunique()}")
    logger.info(f"Unique destination IPs: {df['dst_ip'].nunique()}")

    # Create summary statistics table
    summary_stats = pd.DataFrame(
        {
            "Metric": [
                "Total Flows",
                "Unique Source IPs",
                "Unique Destination IPs",
                "Mean Flow Duration (s)",
                "Max Flow Duration (s)",
                "Min Flow Duration (s)",
                "Mean Packet Size (bytes)",
                "Mean Throughput (bytes/s)",
            ],
            "Value": [
                len(df),
                df["src_ip"].nunique(),
                df["dst_ip"].nunique(),
                f"{df['flow_duration'].mean():.4f}",
                f"{df['flow_duration'].max():.4f}",
                f"{df['flow_duration'].min():.4f}",
                f"{df['pkt_size_avg'].mean():.2f}",
                f"{df['flow_byts_s'].mean():.2f}",
            ],
        }
    )

    # Save summary table
    summary_stats.to_csv(output_dir / "summary_statistics.csv", index=False)
    logger.info(
        f"\nSummary statistics saved to {output_dir / 'summary_statistics.csv'}"
    )
    logger.info(f"\n{summary_stats.to_string(index=False)}")


def classify_flows(df: pd.DataFrame) -> pd.DataFrame:
    """Classify flows based on characteristics."""
    df = df.copy()

    # Classification based on packet characteristics
    conditions = [
        # Large data transfer: high byte count, longer duration
        (df["totlen_bwd_pkts"] > 2000) & (df["flow_duration"] > 0.04),
        # Quick request-response: small packets, fast
        (df["pkt_size_avg"] < 200) & (df["flow_duration"] < 0.05),
        # Interactive session: medium packets, variable timing
        (df["pkt_size_avg"].between(200, 400)) & (df["flow_iat_std"] > 0.01),
        # Bulk transfer: many packets, steady rate
        (df["tot_fwd_pkts"] + df["tot_bwd_pkts"] > 15),
    ]

    choices = ["Large Data", "Quick Request", "Interactive", "Bulk Transfer"]
    df["flow_type"] = pd.Series("Other", index=df.index)

    for condition, choice in zip(conditions, choices):
        df.loc[condition, "flow_type"] = choice

    logger.info("\n=== Flow Classification ===")
    logger.info(f"\n{df['flow_type'].value_counts()}")

    return df


def plot_flow_classification(df: pd.DataFrame, output_dir: Path) -> None:
    """Create pie chart of flow classifications."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Flow type distribution
    flow_counts = df["flow_type"].value_counts()
    colors = sns.color_palette("Set2", len(flow_counts))
    ax1.pie(
        flow_counts.values,
        labels=flow_counts.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
    )
    ax1.set_title("Flow Type Distribution", fontsize=14, fontweight="bold")

    # Flow duration by type
    df.boxplot(column="flow_duration", by="flow_type", ax=ax2)
    ax2.set_title("Flow Duration by Type", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Flow Type", fontsize=12)
    ax2.set_ylabel("Duration (seconds)", fontsize=12)
    plt.suptitle("")  # Remove default title

    plt.tight_layout()
    plt.savefig(output_dir / "flow_classification.png", dpi=300, bbox_inches="tight")
    logger.info(
        f"Flow classification plot saved to {output_dir / 'flow_classification.png'}"
    )
    plt.close()


def analyze_timing_patterns(df: pd.DataFrame, output_dir: Path) -> None:
    """Analyze timing patterns in flows with visualizations."""
    logger.info("\n=== Timing Pattern Analysis ===")

    # Group by rough timing characteristics
    df["timing_category"] = pd.cut(
        df["flow_iat_mean"],
        bins=[0, 0.001, 0.01, 0.1, float("inf")],
        labels=["Very Fast", "Fast", "Medium", "Slow"],
    )

    logger.info(f"\nTiming distribution:\n{df['timing_category'].value_counts()}")

    # Burst vs steady traffic
    df["traffic_pattern"] = "Steady"
    df.loc[df["flow_iat_std"] > df["flow_iat_mean"], "traffic_pattern"] = "Bursty"

    logger.info(f"\nTraffic pattern:\n{df['traffic_pattern'].value_counts()}")

    # Create timing visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Timing category distribution
    timing_counts = df["timing_category"].value_counts()
    axes[0, 0].bar(
        range(len(timing_counts)),
        timing_counts.values,
        color=sns.color_palette("viridis", len(timing_counts)),
    )
    axes[0, 0].set_xticks(range(len(timing_counts)))
    axes[0, 0].set_xticklabels(timing_counts.index, rotation=45)
    axes[0, 0].set_title("Timing Category Distribution", fontsize=12, fontweight="bold")
    axes[0, 0].set_ylabel("Count", fontsize=10)

    # 2. Traffic pattern distribution
    pattern_counts = df["traffic_pattern"].value_counts()
    axes[0, 1].pie(
        pattern_counts.values,
        labels=pattern_counts.index,
        autopct="%1.1f%%",
        colors=sns.color_palette("Set3"),
    )
    axes[0, 1].set_title("Traffic Pattern Distribution", fontsize=12, fontweight="bold")

    # 3. Flow IAT mean histogram
    axes[1, 0].hist(df["flow_iat_mean"], bins=30, color="skyblue", edgecolor="black")
    axes[1, 0].set_title(
        "Flow Inter-Arrival Time Mean Distribution", fontsize=12, fontweight="bold"
    )
    axes[1, 0].set_xlabel("IAT Mean (seconds)", fontsize=10)
    axes[1, 0].set_ylabel("Frequency", fontsize=10)
    axes[1, 0].set_yscale("log")

    # 4. IAT mean vs std scatter
    axes[1, 1].scatter(
        df["flow_iat_mean"],
        df["flow_iat_std"],
        alpha=0.6,
        c=df["traffic_pattern"].map({"Steady": 0, "Bursty": 1}),
        cmap="coolwarm",
    )
    axes[1, 1].set_title(
        "IAT Mean vs Standard Deviation", fontsize=12, fontweight="bold"
    )
    axes[1, 1].set_xlabel("IAT Mean (seconds)", fontsize=10)
    axes[1, 1].set_ylabel("IAT Std Dev (seconds)", fontsize=10)
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_dir / "timing_analysis.png", dpi=300, bbox_inches="tight")
    logger.info(f"Timing analysis plot saved to {output_dir / 'timing_analysis.png'}")
    plt.close()


def analyze_packet_sizes(df: pd.DataFrame, output_dir: Path) -> None:
    """Analyze packet size distributions with visualizations."""
    logger.info("\n=== Packet Size Analysis ===")

    logger.info(f"Average forward packet size: {df['fwd_pkt_len_mean'].mean():.2f}")
    logger.info(f"Average backward packet size: {df['bwd_pkt_len_mean'].mean():.2f}")
    logger.info(f"Overall average packet size: {df['pkt_size_avg'].mean():.2f}")

    # Create packet size summary table
    size_summary = pd.DataFrame(
        {
            "Direction": ["Forward", "Backward", "Overall"],
            "Mean (bytes)": [
                df["fwd_pkt_len_mean"].mean(),
                df["bwd_pkt_len_mean"].mean(),
                df["pkt_size_avg"].mean(),
            ],
            "Max (bytes)": [
                df["fwd_pkt_len_max"].max(),
                df["bwd_pkt_len_max"].max(),
                df["pkt_len_max"].max(),
            ],
            "Min (bytes)": [
                df["fwd_pkt_len_min"].min(),
                df["bwd_pkt_len_min"].min(),
                df["pkt_len_min"].min(),
            ],
        }
    )
    size_summary.to_csv(output_dir / "packet_size_summary.csv", index=False)
    logger.info(f"\n{size_summary.to_string(index=False)}")

    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Forward vs Backward packet size comparison
    axes[0, 0].scatter(
        df["fwd_pkt_len_mean"], df["bwd_pkt_len_mean"], alpha=0.6, c="steelblue"
    )
    axes[0, 0].plot(
        [0, df[["fwd_pkt_len_mean", "bwd_pkt_len_mean"]].max().max()],
        [0, df[["fwd_pkt_len_mean", "bwd_pkt_len_mean"]].max().max()],
        "r--",
        alpha=0.5,
        label="Equal size line",
    )
    axes[0, 0].set_title(
        "Forward vs Backward Packet Size", fontsize=12, fontweight="bold"
    )
    axes[0, 0].set_xlabel("Forward Packet Mean (bytes)", fontsize=10)
    axes[0, 0].set_ylabel("Backward Packet Mean (bytes)", fontsize=10)
    axes[0, 0].legend()

    # 2. Packet size distribution by category
    df["size_category"] = pd.cut(
        df["pkt_size_avg"],
        bins=[0, 200, 400, 1000, float("inf")],
        labels=["Small", "Medium", "Large", "Very Large"],
    )
    size_counts = df["size_category"].value_counts()
    axes[0, 1].bar(
        range(len(size_counts)),
        size_counts.values,
        color=sns.color_palette("rocket", len(size_counts)),
    )
    axes[0, 1].set_xticks(range(len(size_counts)))
    axes[0, 1].set_xticklabels(size_counts.index)
    axes[0, 1].set_title(
        "Packet Size Category Distribution", fontsize=12, fontweight="bold"
    )
    axes[0, 1].set_ylabel("Count", fontsize=10)

    # 3. Histogram of average packet sizes
    axes[1, 0].hist(df["pkt_size_avg"], bins=30, color="coral", edgecolor="black")
    axes[1, 0].set_title(
        "Average Packet Size Distribution", fontsize=12, fontweight="bold"
    )
    axes[1, 0].set_xlabel("Packet Size (bytes)", fontsize=10)
    axes[1, 0].set_ylabel("Frequency", fontsize=10)

    # 4. Box plot of packet sizes by flow type
    flow_types = df["flow_type"].unique()
    data_to_plot = [
        df[df["flow_type"] == ft]["pkt_size_avg"].values for ft in flow_types
    ]
    bp = axes[1, 1].boxplot(data_to_plot, labels=flow_types, patch_artist=True)
    for patch, color in zip(bp["boxes"], sns.color_palette("Set2", len(flow_types))):
        patch.set_facecolor(color)
    axes[1, 1].set_title("Packet Size by Flow Type", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("Flow Type", fontsize=10)
    axes[1, 1].set_ylabel("Packet Size (bytes)", fontsize=10)
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(output_dir / "packet_size_analysis.png", dpi=300, bbox_inches="tight")
    logger.info(
        f"Packet size analysis plot saved to {output_dir / 'packet_size_analysis.png'}"
    )
    plt.close()


def detect_periodic_traffic(df: pd.DataFrame, output_dir: Path) -> None:
    """Detect periodic/polling behavior with visualization."""
    logger.info("\n=== Periodic Traffic Detection ===")

    # Low IAT variance suggests periodic polling
    df["is_periodic"] = (df["flow_iat_std"] < 0.01) & (df["flow_iat_mean"] > 0.001)

    periodic_count = df["is_periodic"].sum()
    logger.info(f"Periodic/polling flows detected: {periodic_count}")

    if periodic_count > 0:
        logger.info("\nPeriodic flow characteristics:")
        periodic = df[df["is_periodic"]]
        logger.info(f"  Mean interval: {periodic['flow_iat_mean'].mean():.4f}s")
        logger.info(f"  Mean packet size: {periodic['pkt_size_avg'].mean():.2f}")

        # Create periodic traffic visualization
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # 1. Periodic vs Non-periodic distribution
        periodic_counts = df["is_periodic"].value_counts()
        axes[0].pie(
            periodic_counts.values,
            labels=["Non-Periodic", "Periodic"],
            autopct="%1.1f%%",
            colors=sns.color_palette("pastel"),
        )
        axes[0].set_title("Periodic Traffic Detection", fontsize=14, fontweight="bold")

        # 2. Time series of flows (if timestamp available)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df_sorted = df.sort_values("timestamp")
            periodic_mask = df_sorted["is_periodic"]

            axes[1].scatter(
                df_sorted[~periodic_mask].index,
                df_sorted[~periodic_mask]["pkt_size_avg"],
                alpha=0.5,
                label="Non-Periodic",
                s=50,
            )
            axes[1].scatter(
                df_sorted[periodic_mask].index,
                df_sorted[periodic_mask]["pkt_size_avg"],
                alpha=0.7,
                label="Periodic",
                s=50,
                c="red",
            )
            axes[1].set_title(
                "Traffic Pattern Over Time", fontsize=14, fontweight="bold"
            )
            axes[1].set_xlabel("Flow Index", fontsize=12)
            axes[1].set_ylabel("Packet Size (bytes)", fontsize=12)
            axes[1].legend()

        plt.tight_layout()
        plt.savefig(output_dir / "periodic_traffic.png", dpi=300, bbox_inches="tight")
        logger.info(
            f"Periodic traffic plot saved to {output_dir / 'periodic_traffic.png'}"
        )
        plt.close()


def correlation_analysis(df: pd.DataFrame, output_dir: Path) -> None:
    """Analyze correlations between key features with heatmap."""
    logger.info("\n=== Feature Correlations ===")

    # Select key features for correlation
    features = [
        "flow_duration",
        "pkt_size_avg",
        "flow_byts_s",
        "flow_iat_mean",
        "tot_fwd_pkts",
        "tot_bwd_pkts",
        "fwd_pkt_len_mean",
        "bwd_pkt_len_mean",
    ]

    corr_matrix = df[features].corr()

    # Find strong correlations (> 0.7)
    logger.info("\nStrong correlations (> 0.7):")
    strong_corr = []
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) > 0.7:  # type: ignore
                logger.info(f"  {features[i]} <-> {features[j]}: {corr_value:.3f}")
                strong_corr.append(
                    {
                        "Feature 1": features[i],
                        "Feature 2": features[j],
                        "Correlation": corr_value,
                    }
                )

    # Save strong correlations table
    if strong_corr:
        pd.DataFrame(strong_corr).to_csv(
            output_dir / "strong_correlations.csv", index=False
        )

    # Create correlation heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
    )
    plt.title("Feature Correlation Heatmap", fontsize=16, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / "correlation_heatmap.png", dpi=300, bbox_inches="tight")
    logger.info(
        f"Correlation heatmap saved to {output_dir / 'correlation_heatmap.png'}"
    )
    plt.close()


def create_traffic_timeline(df: pd.DataFrame, output_dir: Path) -> None:
    """Create timeline visualization of traffic patterns."""
    if "timestamp" not in df.columns:
        logger.warning("No timestamp column found, skipping timeline visualization")
        return

    logger.info("\n=== Creating Traffic Timeline ===")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df_sorted = df.sort_values("timestamp")
    df_sorted["time_offset"] = (
        df_sorted["timestamp"] - df_sorted["timestamp"].min()
    ).dt.total_seconds()

    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    # 1. Throughput over time
    axes[0].plot(
        df_sorted["time_offset"],
        df_sorted["flow_byts_s"],
        marker="o",
        linestyle="-",
        alpha=0.6,
    )
    axes[0].set_title("Throughput Over Time", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Bytes/s", fontsize=10)
    axes[0].grid(True, alpha=0.3)

    # 2. Packet size over time
    axes[1].scatter(
        df_sorted["time_offset"],
        df_sorted["pkt_size_avg"],
        c=df_sorted["flow_type"].astype("category").cat.codes,
        cmap="viridis",
        alpha=0.6,
    )
    axes[1].set_title(
        "Packet Size Over Time (colored by flow type)", fontsize=12, fontweight="bold"
    )
    axes[1].set_ylabel("Packet Size (bytes)", fontsize=10)
    axes[1].grid(True, alpha=0.3)

    # 3. Flow duration over time
    axes[2].bar(
        df_sorted["time_offset"],
        df_sorted["flow_duration"],
        width=0.1,
        alpha=0.7,
        color="coral",
    )
    axes[2].set_title("Flow Duration Over Time", fontsize=12, fontweight="bold")
    axes[2].set_xlabel("Time (seconds from start)", fontsize=10)
    axes[2].set_ylabel("Duration (s)", fontsize=10)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "traffic_timeline.png", dpi=300, bbox_inches="tight")
    logger.info(f"Traffic timeline saved to {output_dir / 'traffic_timeline.png'}")
    plt.close()


def create_summary_report(df: pd.DataFrame, output_dir: Path) -> None:
    """Create a comprehensive summary report."""
    logger.info("\n=== Creating Summary Report ===")

    report = {
        "Total Flows": len(df),
        "Unique Source IPs": df["src_ip"].nunique(),
        "Unique Destination IPs": df["dst_ip"].nunique(),
        "Average Flow Duration (s)": df["flow_duration"].mean(),
        "Average Throughput (bytes/s)": df["flow_byts_s"].mean(),
        "Average Packet Size (bytes)": df["pkt_size_avg"].mean(),
        "Total Forward Packets": df["tot_fwd_pkts"].sum(),
        "Total Backward Packets": df["tot_bwd_pkts"].sum(),
        "Most Common Flow Type": df["flow_type"].mode()[0],
        "Periodic Flows": df["is_periodic"].sum(),
        "Non-Periodic Flows": (~df["is_periodic"]).sum(),
    }

    report_df = pd.DataFrame(list(report.items()), columns=["Metric", "Value"])
    report_df.to_csv(output_dir / "summary_report.csv", index=False)

    logger.info("\n=== SUMMARY REPORT ===")
    logger.info(f"\n{report_df.to_string(index=False)}")


def main():
    """Main analysis pipeline."""
    csv_path = "/data/flow.csv"
    output_dir = Path("/data/analysis")
    output_dir.mkdir(exist_ok=True)

    if not Path(csv_path).exists():
        logger.error(f"CSV file not found: {csv_path}")
        logger.info("Run: docker compose run cicflowmeter")
        return

    # Load data
    df = load_flow_data(csv_path)

    # Run analyses
    basic_statistics(df, output_dir)
    df = classify_flows(df)

    # Generate visualizations
    plot_flow_classification(df, output_dir)
    analyze_timing_patterns(df, output_dir)
    analyze_packet_sizes(df, output_dir)
    detect_periodic_traffic(df, output_dir)
    correlation_analysis(df, output_dir)
    create_traffic_timeline(df, output_dir)
    create_summary_report(df, output_dir)

    # Export classified flows
    output_path = output_dir / "flows_classified.csv"
    df.to_csv(output_path, index=False)
    logger.info("\n=== Analysis complete ===")
    logger.info(f"Results saved to: {output_dir}/")
    logger.info("  - Classified flows: flows_classified.csv")
    logger.info("  - Summary statistics: summary_statistics.csv")
    logger.info("  - Visualizations: *.png files")


if __name__ == "__main__":
    main()
