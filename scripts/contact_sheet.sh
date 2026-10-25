#!/usr/bin/env bash
# One image showing a whole clip, so the agent (and you) can see what is in it.
#
#   ./contact_sheet.sh clip.mp4 sheet.jpg            # 48 frames, 8 x 6
#   ./contact_sheet.sh clip.mp4 sheet.jpg 6 4        # 24 frames
#
# Frames are spread evenly over the clip; each tile is stamped with its time.
set -euo pipefail
IN="$1"; OUT="$2"; C="${3:-8}"; R="${4:-6}"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
N=$((C * R))
RATE=$(python3 -c "print($N/max(float('$DUR'),0.1))")
FONT=""
for f in /System/Library/Fonts/Supplemental/Arial.ttf /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf; do
  [ -f "$f" ] && FONT="$f" && break
done
STAMP=""
if [ -n "$FONT" ] && ffmpeg -hide_banner -filters 2>/dev/null | grep -q drawtext; then
  STAMP=",drawtext=fontfile=$FONT:text='%{pts\\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6"
fi
ffmpeg -nostdin -hide_banner -v error -y -i "$IN" \
  -vf "fps=$RATE,scale=320:-2$STAMP,tile=${C}x${R}" -frames:v 1 -q:v 3 "$OUT"
echo "$OUT"
