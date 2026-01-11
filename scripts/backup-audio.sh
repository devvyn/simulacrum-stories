#!/bin/bash
# Backup paid audio artifacts to external location
# Usage: ./scripts/backup-audio.sh [destination_dir]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default backup destination - customize this
DEFAULT_BACKUP_DIR="${HOME}/Backups/simulacrum-stories"
BACKUP_DIR="${1:-$DEFAULT_BACKUP_DIR}"

DATE=$(date +%Y-%m-%d)
TARBALL="saltmere-paid-audio-${DATE}.tar.gz"

# Paid artifact directories (relative to project root)
PAID_DIRS=(
    "output/audio/saltmere"
    "output/audio/bumpers"
    "output/audio/bumpers-with-titles"
)

echo "=== Saltmere Audio Backup ==="
echo "Date: ${DATE}"
echo "Destination: ${BACKUP_DIR}"
echo

# Create backup directory if needed
mkdir -p "${BACKUP_DIR}"

# Check what we're backing up
echo "Paid artifacts to backup:"
TOTAL_SIZE=0
for dir in "${PAID_DIRS[@]}"; do
    if [[ -d "${PROJECT_DIR}/${dir}" ]]; then
        SIZE=$(du -sh "${PROJECT_DIR}/${dir}" | cut -f1)
        COUNT=$(find "${PROJECT_DIR}/${dir}" -type f \( -name "*.mp3" -o -name "*.wav" \) | wc -l | tr -d ' ')
        echo "  ${dir}: ${SIZE} (${COUNT} files)"
    else
        echo "  ${dir}: (not found)"
    fi
done
echo

# Create tarball
echo "Creating backup tarball..."
cd "${PROJECT_DIR}"
tar -czf "${BACKUP_DIR}/${TARBALL}" \
    --exclude='*.DS_Store' \
    "${PAID_DIRS[@]}"

# Verify
FINAL_SIZE=$(ls -lh "${BACKUP_DIR}/${TARBALL}" | awk '{print $5}')
echo
echo "Backup complete:"
echo "  File: ${BACKUP_DIR}/${TARBALL}"
echo "  Size: ${FINAL_SIZE}"

# Show recent backups
echo
echo "Recent backups in ${BACKUP_DIR}:"
ls -lht "${BACKUP_DIR}"/saltmere-paid-audio-*.tar.gz 2>/dev/null | head -5 || echo "  (none found)"

# Cleanup old backups (keep last 5)
echo
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/saltmere-paid-audio-*.tar.gz 2>/dev/null | wc -l | tr -d ' ')
if [[ ${BACKUP_COUNT} -gt 5 ]]; then
    echo "Cleaning up old backups (keeping last 5)..."
    ls -1t "${BACKUP_DIR}"/saltmere-paid-audio-*.tar.gz | tail -n +6 | xargs rm -f
    echo "  Removed $((BACKUP_COUNT - 5)) old backup(s)"
fi

echo
echo "Done. Remember to copy to additional locations for redundancy."
