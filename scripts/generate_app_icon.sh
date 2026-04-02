#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-/Users/pierre/Code/CortexOSLLM/CortexOSApp/Shared/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png}"

magick -size 1024x1024 -define gradient:angle=135 gradient:'#111827-#070B10' \
  -fill '#0B1016' -stroke '#2A3444' -strokewidth 18 -draw "roundrectangle 140,140 884,884 170,170" \
  -stroke '#73839A' -strokewidth 30 \
    -draw "line 230,440 430,440" \
    -draw "line 230,512 430,512" \
    -draw "line 230,584 430,584" \
  -fill '#E0E8F4' -stroke none -draw "roundrectangle 430,388 602,636 34,34" \
  -stroke '#F97316' -strokewidth 42 -draw "line 602,512 780,512" \
  -fill '#F97316' -stroke '#FDBA74' -strokewidth 10 -draw "roundrectangle 770,444 884,580 28,28" \
  "$OUT"
