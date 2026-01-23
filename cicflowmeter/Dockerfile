FROM python:3.12-slim

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y git libpcap-dev tcpdump && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package installer)
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN pip install uv

# Clone the CICFlowMeter repository
WORKDIR /app
RUN git clone https://github.com/hieulw/cicflowmeter.git && \
    cd cicflowmeter && \
    uv sync

# Set up the environment and install the package
# WORKDIR /app/cicflowmeter
# RUN source .venv/bin/activate && \
#     pip install -e .

# Set the default command to run CICFlowMeter
WORKDIR /app/cicflowmeter
ENTRYPOINT ["sh", "-c"]
CMD ["uv run cicflowmeter -f /pcaps/encrypted-traffic.pcap -c /output/flow.csv"]
