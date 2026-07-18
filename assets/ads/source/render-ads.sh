#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$script_dir"

work_dir=${TMPDIR:-/tmp}/yubios-ad-render
config_dir=$work_dir/config
cache_dir=$work_dir/cache
mkdir -p "$work_dir" "$config_dir" "$cache_dir"

export HOME=$work_dir
export XDG_CONFIG_HOME=$config_dir
export XDG_CACHE_HOME=$cache_dir

render_svg() {
  svg=$1
  output=$2
  logo_size=$3
  logo_radius=$4
  logo_x=$5
  logo_y=$6

  inkscape "$svg" --export-type=png --export-filename="../$output" >/dev/null

  convert ../../logo.png \
    -resize "${logo_size}x${logo_size}!" \
    \( -size "${logo_size}x${logo_size}" xc:none \
       -fill white \
       -draw "roundrectangle 0,0,$((logo_size - 1)),$((logo_size - 1)),$logo_radius,$logo_radius" \) \
    -alpha off -compose CopyOpacity -composite \
    "$work_dir/logo.png"

  convert "../$output" "$work_dir/logo.png" \
    -geometry "+${logo_x}+${logo_y}" -compose over -composite \
    -alpha off -strip "$work_dir/composited.png"

  mv "$work_dir/composited.png" "../$output"
}

render_svg ad-square-1080x1080.svg yubios-ad-square-1080x1080.png 128 28 72 72
render_svg ad-landscape-1200x628.svg yubios-ad-landscape-1200x628.png 274 58 862 154
render_svg ad-medium-rectangle-300x250.svg yubios-ad-medium-rectangle-300x250.png 48 11 18 17
render_svg ad-leaderboard-728x90.svg yubios-ad-leaderboard-728x90.png 64 14 14 13
render_svg ad-skyscraper-160x600.svg yubios-ad-skyscraper-160x600.png 88 21 36 30

render_svg ad-linux-penguin-banner-970x250.svg yubios-ad-linux-penguin-banner-970x250.png 66 15 28 22
convert ../yubios-ad-linux-penguin-banner-970x250.png linux-penguin-foundation.png \
  -geometry +540+0 -compose over -composite \
  "$work_dir/penguin-composited.png"
convert "$work_dir/penguin-composited.png" "$work_dir/logo.png" \
  -geometry +28+22 -compose over -composite \
  -font Helvetica -pointsize 8.4 -fill '#776d80' -gravity southeast \
  -annotate +28+8 'Penguin concept: Larry Ewing & The GIMP.' \
  -alpha off -strip "$work_dir/final-penguin.png"
mv "$work_dir/final-penguin.png" ../yubios-ad-linux-penguin-banner-970x250.png

identify ../yubios-ad-*.png
