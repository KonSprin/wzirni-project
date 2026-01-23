# CICFlowMeter Analysis

This guide covers using CICFlowMeter to extract network flow features and analyzing them with the flow analyzer.

## Overview

CICFlowMeter extracts statistical features from network traffic PCAP files.
These features enable traffic analysis and classification even when the payload is encrypted.

**Key Concept**: While TLS encryption hides content, traffic patterns (timing, packet sizes, flow duration)
reveal behavioral fingerprints that can identify application types and user activities.

## CICFlowMeter Features

CICFlowMeter generates 83 features per network flow, organized into categories:

### Basic Flow Information

- `src_ip`, `dst_ip` - Source and destination IP addresses
- `src_port`, `dst_port` - Source and destination ports
- `protocol` - Protocol number (6=TCP, 17=UDP)
- `timestamp` - Flow start time
- `flow_duration` - Total flow duration in seconds

### Packet Statistics

- `tot_fwd_pkts`, `tot_bwd_pkts` - Total packets in each direction
- `totlen_fwd_pkts`, `totlen_bwd_pkts` - Total bytes in each direction
- `pkt_len_max`, `pkt_len_min`, `pkt_len_mean` - Packet size statistics
- `pkt_size_avg` - Average packet size across flow

### Timing Features

- `flow_iat_mean`, `flow_iat_std` - Inter-arrival time statistics
- `fwd_iat_mean`, `bwd_iat_mean` - Directional inter-arrival times
- `active_mean`, `idle_mean` - Active and idle period statistics

### Throughput Metrics

- `flow_byts_s` - Bytes per second
- `flow_pkts_s` - Packets per second
- `fwd_pkts_s`, `bwd_pkts_s` - Directional packet rates

### TCP Flags

- `fin_flag_cnt`, `syn_flag_cnt`, `rst_flag_cnt` - Connection state flags
- `psh_flag_cnt`, `ack_flag_cnt`, `urg_flag_cnt` - Data transfer flags

## Running CICFlowMeter

### Using Docker Compose

```bash
# Ensure you have captured traffic first
docker compose up server client sniffer

# Wait for some traffic to be captured (30+ seconds)

# Run CICFlowMeter on encrypted traffic
docker compose run --rm cicflowmeter

# Or on decrypted traffic
docker compose run --rm cicflowmeter sh -c \
  "uv run cicflowmeter -f /pcaps/proxy-*.pcap -c /output/flow_decrypted.csv"
```

### Output Location

Flow CSV files are saved to `./cicflowmeter/output/`:

- `flow.csv` - Features from encrypted traffic
- `flow_decrypted.csv` - Features from decrypted traffic (if analyzed)

## Flow Analysis

The `flow_analyzer.py` script processes CICFlowMeter output to extract insights and generate visualizations.

### Running the Analyzer

```bash
# Install dependencies (if running locally)
poetry install

# Run analysis
poetry run python flow_analyzer.py
```

### Analysis Output

All results are saved to `./cicflowmeter/output/analysis/`:

#### Tables (CSV)

1. **summary_statistics.csv**
   - Total flows, unique IPs
   - Duration statistics
   - Average packet size and throughput

2. **packet_size_summary.csv**
   - Mean, max, min packet sizes
   - Breakdown by direction (forward/backward)

3. **strong_correlations.csv**
   - Feature pairs with correlation > 0.7
   - Helps identify redundant or related features

4. **summary_report.csv**
   - Comprehensive overview
   - Flow type distribution
   - Periodic traffic detection results

5. **flows_classified.csv**
   - Original flow data with added classifications
   - `flow_type` - Classified traffic type
   - `timing_category` - Fast/medium/slow
   - `traffic_pattern` - Steady/bursty
   - `is_periodic` - Periodic traffic detection

#### Visualizations (PNG)

1. **flow_classification.png**
   - Pie chart: Distribution of flow types
   - Box plot: Flow duration by type

2. **timing_analysis.png**
   - Timing category distribution
   - Traffic pattern (steady vs bursty)
   - IAT mean histogram
   - IAT mean vs standard deviation scatter plot

3. **packet_size_analysis.png**
   - Forward vs backward packet size scatter
   - Packet size category distribution
   - Packet size histogram
   - Packet size by flow type box plot

4. **periodic_traffic.png**
   - Periodic vs non-periodic distribution
   - Traffic patterns over time

5. **correlation_heatmap.png**
   - Correlation matrix of key features
   - Identifies relationships between metrics

6. **traffic_timeline.png**
   - Throughput over time
   - Packet size over time (colored by flow type)
   - Flow duration over time

## Flow Classification

The analyzer automatically classifies flows into categories:

### Large Data Transfer

- **Characteristics**: High backward byte count (>2000), longer duration (>0.04s)
- **Example**: GET /data/large endpoint responses

### Quick Request

- **Characteristics**: Small packets (<200 bytes), fast (<0.05s)
- **Example**: Health checks, simple API calls

### Interactive

- **Characteristics**: Medium packets (200-400 bytes), variable timing
- **Example**: User login, message sending

### Bulk Transfer

- **Characteristics**: Many packets (>15 total)
- **Example**: Large dataset retrieval, file transfers

### Other

- Flows that don't match specific patterns

## Traffic Pattern Detection

### Timing Categories

Based on `flow_iat_mean`:

- **Very Fast**: <0.001s - Rapid exchanges
- **Fast**: 0.001-0.01s - Normal API responses
- **Medium**: 0.01-0.1s - Interactive sessions
- **Slow**: >0.1s - Long-running connections

### Traffic Patterns

Based on IAT variability:

- **Steady**: IAT std < IAT mean - Consistent timing
- **Bursty**: IAT std > IAT mean - Variable timing

### Periodic Traffic

Detected when:

- Low IAT variance (std < 0.01)
- Non-zero IAT mean (> 0.001)

**Indicates**: Polling behavior, scheduled tasks, keep-alive messages

## Interpreting Results

### Example Analysis

Given this flow:

```csv
src_ip,dst_ip,flow_duration,pkt_size_avg,flow_byts_s,tot_fwd_pkts,tot_bwd_pkts
172.21.0.3,172.21.0.2,0.099,163.79,31372,12,7
```

**Interpretation**:

- Duration: 99ms - quick interaction
- Packet size: 164 bytes average - small payload
- Throughput: 31KB/s - moderate
- Asymmetry: 12 forward, 7 backward - typical request/response
- **Likely**: API call with small request, moderate response

### Comparing Encrypted vs Decrypted

**Key Insight**: Flow features are nearly identical for encrypted and decrypted traffic.

Differences:

- Encrypted traffic has TLS handshake overhead
- Encrypted packets slightly larger due to TLS headers
- Timing may vary slightly due to encryption/decryption

**Conclusion**: Statistical analysis works on encrypted traffic without decryption.

## Use Cases

### 1. Application Fingerprinting

Identify applications by traffic patterns:

- **Login**: Small symmetric packets, quick duration
- **Messaging**: Medium packets, interactive timing
- **Streaming**: Large asymmetric flows, steady pattern
- **File Transfer**: Very large flows, bulk pattern

### 2. Anomaly Detection

Detect unusual behavior:

- Unexpected packet sizes for known endpoints
- Abnormal timing patterns
- Unusual flow durations
- Traffic volume spikes

### 3. Quality of Service (QoS)

Classify traffic for prioritization:

- Interactive traffic (gaming, VoIP): low latency needed
- Bulk transfer (downloads): high bandwidth needed
- Periodic polling: predictable resource usage

### 4. Security Analysis

Identify potential threats:

- Port scanning: many short flows to different ports
- Data exfiltration: large outbound transfers
- Command & control: periodic beaconing patterns
- DDoS: high packet rate, small packet size

## Advanced Analysis

### Machine Learning Opportunities

The classified flows can be used to train ML models:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load classified flows
df = pd.read_csv('cicflowmeter/output/analysis/flows_classified.csv')

# Select features
features = ['flow_duration', 'pkt_size_avg', 'flow_byts_s',
            'flow_iat_mean', 'tot_fwd_pkts', 'tot_bwd_pkts']
X = df[features]
y = df['flow_type']

# Train classifier
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Predict flow types
predictions = clf.predict(X_test)
```

### Custom Feature Engineering

Add domain-specific features:

```python
# Request/response ratio
df['fwd_bwd_ratio'] = df['tot_fwd_pkts'] / df['tot_bwd_pkts']

# Payload efficiency
df['payload_ratio'] = (
    df['totlen_fwd_pkts'] / (df['tot_fwd_pkts'] * df['fwd_header_len'])
)

# Burst detection
df['is_burst'] = (df['flow_iat_std'] > 2 * df['flow_iat_mean'])
```

## Troubleshooting

### No Flow Data Generated

**Problem**: CICFlowMeter produces empty CSV

**Solutions**:

1. Ensure traffic was captured:

   ```bash
   ls -lh ./sniffer/captures/encrypted-traffic.pcap
   ```

2. Check PCAP file has data:

   ```bash
   tcpdump -r ./sniffer/captures/encrypted-traffic.pcap -c 10
   ```

3. Verify CICFlowMeter parameters:

   ```bash
   docker compose run --rm cicflowmeter sh -c \
     "uv run cicflowmeter -f /pcaps/encrypted-traffic.pcap -c /output/test.csv"
   ```

### Analysis Script Fails

**Problem**: flow_analyzer.py crashes or produces no output

**Solutions**:

1. Check CSV exists:

   ```bash
   ls -lh ./cicflowmeter/output/flow.csv
   ```

2. Verify CSV format:

   ```bash
   head -n 2 ./cicflowmeter/output/flow.csv
   ```

3. Install missing dependencies:

   ```bash
   poetry install
   ```

4. Check for NaN values:

   ```python
   import pandas as pd
   df = pd.read_csv('cicflowmeter/output/flow.csv')
   print(df.isnull().sum())
   ```

### Missing Visualizations

**Problem**: PNG files not generated

**Solutions**:

1. Ensure matplotlib backend is set:

   ```bash
   export MPLBACKEND=Agg
   python flow_analyzer.py
   ```

2. Check directory permissions:

   ```bash
   mkdir -p cicflowmeter/output/analysis
   chmod 755 cicflowmeter/output/analysis
   ```

3. Run with verbose logging:

   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

## Best Practices

1. **Capture Sufficient Traffic**
   - Run client for at least 1-2 minutes before analysis
   - More flows = more reliable patterns

2. **Compare Encrypted vs Decrypted**
   - Analyze both to understand what statistical analysis reveals
   - Validate that features are consistent

3. **Regular Analysis**
   - Run CICFlowMeter periodically during long captures
   - Monitor traffic patterns over time

4. **Feature Selection**
   - Not all 83 features are useful for every task
   - Use correlation analysis to identify redundant features
   - Focus on features relevant to your use case

5. **Document Findings**
   - Save classification rules for reproducibility
   - Note which features are most discriminative
   - Track accuracy of pattern detection

## Further Reading

- [CICFlowMeter GitHub](https://github.com/hieulw/cicflowmeter) - Official documentation
- [CICIDS2017 Dataset](https://www.unb.ca/cic/datasets/ids-2017.html) - Example dataset using these features
- Network Traffic Analysis with Flow Data - Research papers on ML classification
- [Wireshark Statistics](https://wiki.wireshark.org/Statistics) - Complementary analysis tools
