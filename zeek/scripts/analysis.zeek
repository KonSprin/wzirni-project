@load base/protocols/ssl
@load base/protocols/http
@load policy/protocols/ssl/validate-certs

# This minimal script just enables default logging
# Zeek will automatically generate:
# - conn.log (all connections)
# - ssl.log (TLS metadata including certificates, ciphers, SNI)
# - http.log (HTTP requests/responses if decrypted)
# - files.log (file transfers)

# Optional: Add custom annotations to connections
event ssl_established(c: connection) {
    if (c?$ssl && c$ssl?$server_name) {
        # You can add custom logic here
        # For now, just let Zeek do its default logging
    }
}

event connection_state_remove(c: connection) {
    # Connection finished, logs are automatically written
}
