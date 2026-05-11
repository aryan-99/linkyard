#!/usr/bin/env bash
# =============================================================================
# block_egress_private.sh — Outbound egress firewall for Linkyard backend
# =============================================================================
#
# PURPOSE
#   Blocks outbound TCP connections from the container to private / internal
#   address ranges.  This is a defense-in-depth layer against DNS-rebinding
#   attacks: even if application-level SSRF guards are bypassed (e.g. via a
#   TTL-0 rebind), the kernel will drop the packet before it leaves the
#   network namespace.
#
# RANGES BLOCKED
#   IPv4:
#     10.0.0.0/8         RFC-1918 private (class A)
#     172.16.0.0/12      RFC-1918 private (class B)
#     192.168.0.0/16     RFC-1918 private (class C)
#     127.0.0.0/8        Loopback
#     169.254.0.0/16     Link-local / AWS instance-metadata (169.254.169.254)
#   IPv6:
#     ::1/128            Loopback
#     fc00::/7           Unique-local (fd00::/8 + fc00::/8)
#
# WHEN TO RUN
#   At container startup, *before* uvicorn is launched.  The entrypoint
#   script (or CMD in the Dockerfile) must run this as root and then
#   exec/drop to the app process.  Running it after the app starts is still
#   better than not running it at all, but a small window exists.
#
# IDEMPOTENCY
#   Each rule is checked with iptables -C / ip6tables -C before insertion.
#   Re-running the script on an already-configured namespace is a no-op.
#
# REQUIREMENTS
#   iptables and ip6tables must be installed inside the container image
#   (apt-get install -y iptables).  The process must run as root (or with
#   CAP_NET_ADMIN) when this script executes.
# =============================================================================

set -euo pipefail

# ── helpers ──────────────────────────────────────────────────────────────────

add_ipv4_rule() {
    local dest="$1"
    if ! iptables -C OUTPUT -d "$dest" -p tcp -j DROP 2>/dev/null; then
        iptables -A OUTPUT -d "$dest" -p tcp -j DROP
        echo "[egress] blocked IPv4 $dest"
    else
        echo "[egress] rule already present for IPv4 $dest — skipping"
    fi
}

add_ipv6_rule() {
    local dest="$1"
    if ! ip6tables -C OUTPUT -d "$dest" -p tcp -j DROP 2>/dev/null; then
        ip6tables -A OUTPUT -d "$dest" -p tcp -j DROP
        echo "[egress] blocked IPv6 $dest"
    else
        echo "[egress] rule already present for IPv6 $dest — skipping"
    fi
}

# ── IPv4 rules ────────────────────────────────────────────────────────────────

add_ipv4_rule "10.0.0.0/8"        # RFC-1918 class A
add_ipv4_rule "172.16.0.0/12"     # RFC-1918 class B
add_ipv4_rule "192.168.0.0/16"    # RFC-1918 class C
add_ipv4_rule "127.0.0.0/8"       # loopback
add_ipv4_rule "169.254.0.0/16"    # link-local / AWS metadata service

# ── IPv6 rules ────────────────────────────────────────────────────────────────

add_ipv6_rule "::1/128"           # loopback
add_ipv6_rule "fc00::/7"          # unique-local (fc00::/8 + fd00::/8)

echo "[egress] egress firewall applied."
