import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_flow_data(csv_path: str) -> pd.DataFrame:
    """Load CICFlowMeter CSV data."""
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} flows from {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise


def basic_statistics(df: pd.DataFrame) -> None:
    """Display basic flow statistics."""
    logger.info("=== Basic Flow Statistics ===")
    logger.info(f"Total flows: {len(df)}")
    logger.info(f"Unique source IPs: {df['src_ip'].nunique()}")
    logger.info(f"Unique destination IPs: {df['dst_ip'].nunique()}")
    logger.info(f"Protocol distribution:\n{df['protocol'].value_counts()}")

    logger.info("\n=== Flow Duration Statistics ===")
    logger.info(f"Mean duration: {df['flow_duration'].mean():.4f}s")
    logger.info(f"Max duration: {df['flow_duration'].max():.4f}s")
    logger.info(f"Min duration: {df['flow_duration'].min():.4f}s")


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


def analyze_timing_patterns(df: pd.DataFrame) -> None:
    """Analyze timing patterns in flows."""
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


def analyze_packet_sizes(df: pd.DataFrame) -> None:
    """Analyze packet size distributions."""
    logger.info("\n=== Packet Size Analysis ===")

    logger.info(f"Average forward packet size: {df['fwd_pkt_len_mean'].mean():.2f}")
    logger.info(f"Average backward packet size: {df['bwd_pkt_len_mean'].mean():.2f}")
    logger.info(f"Overall average packet size: {df['pkt_size_avg'].mean():.2f}")

    # Identify potential endpoint types by packet size
    logger.info("\n=== Potential Activity by Packet Patterns ===")

    # Small consistent packets - likely auth/control
    small_pkts = df[df["pkt_size_avg"] < 200]
    logger.info(f"Small packet flows (auth/control): {len(small_pkts)}")

    # Medium packets - typical API calls
    medium_pkts = df[df["pkt_size_avg"].between(200, 400)]
    logger.info(f"Medium packet flows (API calls): {len(medium_pkts)}")

    # Large packets - data transfer
    large_pkts = df[df["pkt_size_avg"] > 400]
    logger.info(f"Large packet flows (data transfer): {len(large_pkts)}")


def detect_periodic_traffic(df: pd.DataFrame) -> None:
    """Detect periodic/polling behavior."""
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


def correlation_analysis(df: pd.DataFrame) -> None:
    """Analyze correlations between key features."""
    logger.info("\n=== Feature Correlations ===")

    # Select key features for correlation
    features = [
        "flow_duration",
        "pkt_size_avg",
        "flow_byts_s",
        "flow_iat_mean",
        "tot_fwd_pkts",
        "tot_bwd_pkts",
    ]

    corr_matrix = df[features].corr()

    # Find strong correlations (> 0.7)
    logger.info("\nStrong correlations (> 0.7):")
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) > 0.7:  # type: ignore
                logger.info(f"  {features[i]} <-> {features[j]}: {corr_value:.3f}")


def main():
    """Main analysis pipeline."""
    csv_path = "/data/flow.csv"

    if not Path(csv_path).exists():
        logger.error(f"CSV file not found: {csv_path}")
        logger.info("Run: docker compose run cicflowmeter")
        return

    # Load data
    df = load_flow_data(csv_path)

    # Run analyses
    basic_statistics(df)
    df = classify_flows(df)
    analyze_timing_patterns(df)
    analyze_packet_sizes(df)
    detect_periodic_traffic(df)
    correlation_analysis(df)

    # Export classified flows
    output_path = "/data/flows_classified.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"\n=== Analysis complete. Classified flows saved to {output_path} ===")


if __name__ == "__main__":
    main()
