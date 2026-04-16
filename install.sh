#!/usr/bin/env bash
# install.sh — install dockgen to ~/.local (default) or system-wide (with --system)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM=0
EDITABLE=0

usage() {
    echo "Usage: $0 [--system] [--editable]"
    echo "  --system     install to /usr/local (requires sudo)"
    echo "  --editable   pip install -e (dev mode, stays linked to source)"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --system)   SYSTEM=1 ;;
        --editable) EDITABLE=1 ;;
        -h|--help)  usage ;;
        *) echo "unknown option: $1"; usage ;;
    esac
    shift
done

# ── check Python ────────────────────────────────────────────────────────────
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" \
    || { echo "error: Python 3.8+ required (found $(python3 --version))"; exit 1; }

echo "Python $(python3 --version) ✓"

# ── install package ──────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

_install_package() {
    if [[ $SYSTEM -eq 1 ]]; then
        pip3 install ${EDITABLE:+-e} .
        return
    fi
    # Prefer pipx for user installs on modern distros (avoids PEP 668 errors)
    if command -v pipx &>/dev/null && [[ $EDITABLE -eq 0 ]]; then
        pipx install --force .
        return
    fi
    # Fall back to pip --user; add --break-system-packages if the distro needs it
    if pip3 install --user ${EDITABLE:+-e} . 2>&1 | grep -q "externally-managed"; then
        echo "note: externally-managed env detected; retrying with --break-system-packages"
        pip3 install --user ${EDITABLE:+-e} --break-system-packages .
    else
        pip3 install --user ${EDITABLE:+-e} .
    fi
}

_install_package
echo "dockgen package installed ✓"

# ── bash completion ──────────────────────────────────────────────────────────
if [[ $SYSTEM -eq 1 ]]; then
    COMP_DIR="/etc/bash_completion.d"
    MAN_DIR="/usr/local/share/man/man1"
else
    COMP_DIR="$HOME/.local/share/bash-completion/completions"
    MAN_DIR="$HOME/.local/share/man/man1"
fi

if [[ -d "$COMP_DIR" ]] || mkdir -p "$COMP_DIR" 2>/dev/null; then
    install -m 644 completions/dockgen.bash "$COMP_DIR/dockgen"
    echo "bash completion → $COMP_DIR/dockgen ✓"
else
    echo "note: could not write completion to $COMP_DIR; skipping"
fi

# ── man page ─────────────────────────────────────────────────────────────────
if mkdir -p "$MAN_DIR" 2>/dev/null; then
    install -m 644 man/dockgen.1 "$MAN_DIR/dockgen.1"
    # compress if gzip is available
    if command -v gzip &>/dev/null; then
        gzip -f "$MAN_DIR/dockgen.1"
        echo "man page     → $MAN_DIR/dockgen.1.gz ✓"
    else
        echo "man page     → $MAN_DIR/dockgen.1 ✓"
    fi
else
    echo "note: could not write man page to $MAN_DIR; skipping"
fi

# ── PATH reminder ─────────────────────────────────────────────────────────────
if [[ $SYSTEM -eq 0 ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "  ⚠  ~/.local/bin is not in PATH. Add it:"
    echo "     echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "     source ~/.bashrc"
fi

echo ""
echo "Done. Run: dockgen --help"
