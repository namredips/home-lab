#!/usr/bin/env bash
# Download community Grafana dashboards to replace the placeholder stubs.
# Run this on the monitoring VM after deployment:
#   bash /opt/monitoring/grafana/dashboards/download-community-dashboards.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

download_dashboard() {
  local id="$1"
  local filename="$2"
  local dest="${SCRIPT_DIR}/${filename}"
  echo "Downloading dashboard #${id} → ${filename}"
  curl -fsSL "https://grafana.com/api/dashboards/${id}/revisions/latest/download" \
    -o "${dest}"
  echo "  ✓ ${filename} ($(wc -c < "${dest}") bytes)"
}

echo "=== Downloading community Grafana dashboards ==="
download_dashboard 1860  "node-exporter-full.json"
download_dashboard 2842  "ceph-cluster.json"
download_dashboard 10347 "proxmox-ve.json"

echo ""
echo "=== Restarting Grafana to pick up new dashboards ==="
docker compose -f /opt/monitoring/docker-compose.yml restart grafana
echo "Done. Dashboards available at http://10.220.1.63:3000"
