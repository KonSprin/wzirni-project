#!/bin/bash
set -e

# Copy certificates if they exist (this part runs as root initially)
if [ -f /certs/polarproxy.crt ]; then
    cp /certs/polarproxy.crt /usr/local/share/ca-certificates/
fi

# Update CA certificates
update-ca-certificates

# Execute the CMD
exec "$@"
