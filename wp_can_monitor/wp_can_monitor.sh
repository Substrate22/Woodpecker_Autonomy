#!/usr/bin/env bash

# Shion Britten Spring 2026 Multidiscplinary Capstone at OSU
# can_tools.sh — CAN bus utility script for Woodpecker LSEV
# using can-utils linux library and cantools Python library

# ── Resolve script directory (portable) ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_ACTIVATE="$SCRIPT_DIR/canenv/bin/activate"
DBC_DIR="$SCRIPT_DIR/dbc"
DBC_FILE="/dbc/woodpecker_12v_modules.dbc"

CAN_IFACE="can0"
BAUDRATE="500000"

# ── Helper functions ──────────────────────────────────────────────────────────
die(){
    echo "Error: $*" >&2;
    exit 1;
}

activate_venv(){
    #check if venv is properly configured
    if [[! -d "$SCRIPT_DIR/canenv"]]; then
        echo "Virtual environment not found, creating one..."
        python3 -m venv "$SCRIPT_DIR/canenv" || die "Failed to create virtual environment"
    fi

    #activate venv
    [[ -f "$VENV_ACTIVATE" ]] || die "Virtual environment not found at $VENV_ACTIVATE"
    source "$VENV_ACTIVATE"

    #if cantools is not installed properly config it
    if ! python3 -c "import cantools" &>/dev/null; then
        echo "cantools not found — installing..."
        pip install cantools || die "Failed to install cantools"
    fi
}

require_dbc() {
    local dbc="$DBC_DIR/$1"
    [[ -f "$dbc" ]] || die "DBC file not found: $dbc"
    echo "$dbc"
}

init_CAN(){
    echo "Initializing Woodpecker CAN bus at baud=${BAUDRATE}"
    if sudo ip link set up "$CAN_IFACE" type can bitrate "$BAUDRATE"; then
        echo "Init success!"
    else
        return 1
    fi 
}

decode() {
    local dbc_file
    dbc_file="$(require_dbc "$1")"
    activate_venv
    echo "Decoding with $(basename "$dbc_file") — press Ctrl+C to stop."
    candump "$CAN_IFACE" | python3 -m cantools decode "$dbc_file"
}

log_and_decode() {
    local dbc_file raw_log capture_log
    dbc_file="$(require_dbc "$1")"
    raw_log="${2:-raw_can.log}"
    capture_log="${3:-capture_outfile.log}"
    activate_venv
    echo "Logging raw → $raw_log  |  decoded → $capture_log  — press Ctrl+C to stop."
    candump "$CAN_IFACE" \
        | tee "$raw_log" \
        | python3 -m cantools decode "$dbc_file" \
        | tee "$capture_log"
}

filter_decode() {
    local filter="$1:7FF" dbc_file
    dbc_file="$(require_dbc "$2")"
    activate_venv
    echo "Filtering 0x$1 — press Ctrl+C to stop."
    candump "${CAN_IFACE},${filter}" | python3 -m cantools decode "$dbc_file"
}
 
usage() {
    cat <<EOF
Usage: $(basename "$0") <command> [options]
 
Commands:
  init                    Bring up $CAN_IFACE at ${BAUDRATE} bps
  venv                    Activate virtual environment (activated automatically by decode/log/filter)
  deactivate              Reminder: run 'deactivate' in your shell
 
  decode steering         Decode EPS1/EPS2 CAN messages
  decode brake            Decode DBS CAN messages
  decode throttle         Decode TCM CAN messages
  decode all              Decode all 12 V module CAN messages
 
  log [raw.log] [out.log] Log bus traffic and decode all modules
  filter <HEX:MASK>       Filter messages by CAN ID (e.g. 201 for 0x201 = CommandThrottle)
 
Examples:
  $0 init
  $0 decode steering
  $0 decode all
  $0 log
  $0 log my_raw.log my_decoded.log
  $0 filter 201
EOF
}

# ── DBC map ───────────────────────────────────────────────────────────────────
dbc_for() {
    case "$1" in
        steering)  echo "Woodpecker_Oregon.dbc" ;;
        brake)     echo "DBS3001_231010.dbc" ;;
        throttle)  echo "ican_4404_Woodpecker_Oregon.dbc" ;;
        all)       echo "woodpecker_12v_modules.dbc" ;;
        *)         die "Unknown module '$1'. Choose: steering | brake | throttle | all" 
;;
    esac
}

# ── Main dispatch ─────────────────────────────────────────────────────────────
[[ $# -ge 1 ]] || { usage; exit 0; }
 
CMD="$1"; shift
 
case "$CMD" in
    init)
        init_CAN
        ;;
    venv)
        echo "Run this in your shell to activate the venv:"
        echo "  source $VENV_ACTIVATE"
        ;;
    deactivate)
        echo "Run 'deactivate' directly in your shell to exit the venv."
        ;;
    decode)
        [[ $# -ge 1 ]] || die "'decode' requires a module: steering | brake | throttle | all"
        decode "$(dbc_for "$1")"
        ;;
    log)
        RAW="${1:-raw_can.log}"
        CAPTURE="${2:-capture_outfile.log}"
        log_and_decode "woodpecker_12v_modules.dbc" "$RAW" "$CAPTURE"
        ;;
    filter)
        [[ $# -ge 1 ]] || die "'filter' requires a HEX ID, e.g. 201 CommandThrottle"
        filter_decode "$1" "woodpecker_12v_modules.dbc"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Unknown command: $CMD"
        usage
        exit 1
        ;;
esac
