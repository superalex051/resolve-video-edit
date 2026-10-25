#!/usr/bin/env bash
# Level a finished export to a loudness target without re-encoding the picture.
# Two-pass ffmpeg loudnorm (linear), video stream copied, AAC 320k 48 kHz.
#
#   ./loudnorm_copy.sh "in.mov" "out (-17 LUFS).mov"            # -17 LUFS, -1.5 dBTP
#   ./loudnorm_copy.sh "in.mov" "out (-14 LUFS).mov" -14 -1.0
#
# Prints the measurement before and after. YouTube plays everything at about
# -14 LUFS; -17 to -14 are all fine for upload. Reels and Shorts: -14.
set -euo pipefail
IN="$1"; OUT="$2"; I="${3:--17}"; TP="${4:--1.5}"; LRA=11
[ -e "$OUT" ] && { echo "refusing to overwrite $OUT" >&2; exit 1; }
measure() {
  ffmpeg -nostdin -hide_banner -i "$1" -map 0:a:0 -af "loudnorm=I=$I:TP=$TP:LRA=$LRA:print_format=json" -f null - 2>&1 \
    | awk '/^\{/,/^\}/'
}
M=$(measure "$IN")
get() { echo "$M" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
echo "before: $(get input_i) LUFS, true peak $(get input_tp) dBTP"
ffmpeg -nostdin -hide_banner -v error -i "$IN" -map 0:v:0 -map 0:a:0 -c:v copy \
  -af "loudnorm=I=$I:TP=$TP:LRA=$LRA:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true" \
  -ar 48000 -c:a aac -b:a 320k -movflags +faststart "$OUT"
M=$(measure "$OUT")
echo "after:  $(get input_i) LUFS, true peak $(get input_tp) dBTP"
