#!/usr/bin/env bash
# Record the screen (or one region) for the demo video, capped at 60 s, as a 1080p H.264 MP4
# that X and Reddit accept.
#
#   scripts/record.sh out.mp4                    # whole screen
#   scripts/record.sh out.mp4 1920x1080+0+0      # region WxH+X+Y
#   SECONDS_MAX=45 scripts/record.sh out.mp4     # shorter cap
#
# Press q in this terminal to stop early. Close notifications, browser tabs and anything
# that shows keys or e-mail before recording.
set -euo pipefail
OUT="${1:?usage: record.sh out.mp4 [WxH+X+Y]}"
REGION="${2:-}"
MAX="${SECONDS_MAX:-60}"
DISPLAY_ID="${DISPLAY:?DISPLAY is not set}"

if [[ -n $REGION ]]; then
  SIZE="${REGION%%+*}"; OFFSET="+${REGION#*+}"
else
  SIZE="$(xdpyinfo -display "$DISPLAY_ID" | awk '/dimensions:/{print $2}')"; OFFSET="+0,0"
fi
OFFSET="${OFFSET/+/}"; OFFSET="${OFFSET/+/,}"

mkdir -p "$(dirname "$OUT")"
ffmpeg -hide_banner -loglevel warning -y \
  -f x11grab -framerate 30 -video_size "$SIZE" -i "$DISPLAY_ID+$OFFSET" \
  -t "$MAX" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 20 -movflags +faststart \
  "$OUT"
echo "saved $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | cut -d. -f1) s)"
