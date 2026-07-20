#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ads_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
assets_dir=$(CDPATH= cd -- "$script_dir/../.." && pwd)
logo_file=$assets_dir/logo.png

work_dir=${TMPDIR:-/tmp}/yubios-ad-render
config_dir=$work_dir/config
cache_dir=$work_dir/cache
mkdir -p "$work_dir" "$config_dir" "$cache_dir" \
  "$ads_dir/v1" "$ads_dir/v2" "$ads_dir/v1-upscaled" "$ads_dir/v2-upscaled"

export HOME=$work_dir
export XDG_CONFIG_HOME=$config_dir
export XDG_CACHE_HOME=$cache_dir

render_scale() {
  version=$1
  svg=$2
  output=$3
  width=$4
  height=$5
  logo_size=$6
  logo_radius=$7
  logo_x=$8
  logo_y=$9
  scale=${10}

  output_width=$((width * scale))
  output_height=$((height * scale))
  scaled_logo_size=$((logo_size * scale))
  scaled_logo_radius=$((logo_radius * scale))
  scaled_logo_x=$((logo_x * scale))
  scaled_logo_y=$((logo_y * scale))

  (
    cd "$script_dir/$version"
    inkscape "$svg" \
      --export-type=png \
      --export-width="$output_width" \
      --export-height="$output_height" \
      --export-filename="$work_dir/base.png" >/dev/null
  )

  art_file=$work_dir/base.png
  if [ "$version" = v2 ]; then
    case $svg in
      ad-square-1080x1080.svg) foundation=square-chain.png ;;
      ad-landscape-1200x628.svg) foundation=landscape-chain.png ;;
      ad-medium-rectangle-300x250.svg) foundation=medium-chain.png ;;
      ad-leaderboard-728x90.svg) foundation=leaderboard-chain.png ;;
      ad-skyscraper-160x600.svg) foundation=skyscraper-chain.png ;;
      ad-linux-penguin-banner-970x250.svg) foundation=linux-penguin.png ;;
      *) echo "unknown v2 asset: $svg" >&2; exit 1 ;;
    esac

    if [ "$svg" = ad-linux-penguin-banner-970x250.svg ]; then
      convert "$script_dir/v2/foundations/$foundation" \
        -resize "${output_width}x${output_height}" \
        -gravity east -background '#03040d' \
        -extent "${output_width}x${output_height}" \
        "$work_dir/background.png"
    else
      convert "$script_dir/v2/foundations/$foundation" \
        -resize "${output_width}x${output_height}^" \
        -gravity center \
        -extent "${output_width}x${output_height}" \
        "$work_dir/background.png"
    fi

    convert "$work_dir/background.png" "$work_dir/base.png" \
      -compose over -composite "$work_dir/art.png"
    art_file=$work_dir/art.png
  elif [ "$svg" = ad-linux-penguin-banner-970x250.svg ]; then
    penguin_width=$((430 * scale))
    penguin_height=$((250 * scale))
    penguin_x=$((540 * scale))
    convert "$script_dir/v1/linux-penguin-foundation.png" \
      -resize "${penguin_width}x${penguin_height}!" \
      "$work_dir/v1-penguin.png"
    convert "$work_dir/base.png" "$work_dir/v1-penguin.png" \
      -geometry "+${penguin_x}+0" -compose over -composite \
      "$work_dir/art.png"
    art_file=$work_dir/art.png
  fi

  convert "$logo_file" \
    -resize "${scaled_logo_size}x${scaled_logo_size}!" \
    \( -size "${scaled_logo_size}x${scaled_logo_size}" xc:none \
       -fill white \
       -draw "roundrectangle 0,0,$((scaled_logo_size - 1)),$((scaled_logo_size - 1)),$scaled_logo_radius,$scaled_logo_radius" \) \
    -alpha off -compose CopyOpacity -composite \
    "$work_dir/logo.png"

  final_file=$output
  if [ "$version" = v1 ] && [ "$svg" = ad-linux-penguin-banner-970x250.svg ]; then
    final_file=$work_dir/final.png
  fi

  convert "$art_file" "$work_dir/logo.png" \
    -geometry "+${scaled_logo_x}+${scaled_logo_y}" \
    -compose over -composite \
    -alpha off -strip "$final_file"

  if [ "$version" = v1 ] && [ "$svg" = ad-linux-penguin-banner-970x250.svg ]; then
    if [ "$scale" = 1 ]; then
      point_size=8.4
      legend_x=28
      legend_y=8
    else
      point_size=16.8
      legend_x=56
      legend_y=16
    fi
    convert "$final_file" \
      -font Helvetica -pointsize "$point_size" -fill '#776d80' \
      -gravity southeast -annotate "+${legend_x}+${legend_y}" \
      'Penguin concept: Larry Ewing & The GIMP.' \
      -alpha off -strip "$output"
  fi
}

render_asset() {
  version=$1
  svg=$2
  standard_name=$3
  upscaled_name=$4
  width=$5
  height=$6
  logo_size=$7
  logo_radius=$8
  logo_x=$9
  logo_y=${10}
  render_standard=${11}

  if [ "$render_standard" = 1 ] || [ ! -f "$ads_dir/$version/$standard_name" ]; then
    render_scale "$version" "$svg" "$ads_dir/$version/$standard_name" \
      "$width" "$height" "$logo_size" "$logo_radius" "$logo_x" "$logo_y" 1
  fi

  render_scale "$version" "$svg" "$ads_dir/${version}-upscaled/$upscaled_name" \
    "$width" "$height" "$logo_size" "$logo_radius" "$logo_x" "$logo_y" 2
}

render_v1_standard=${RENDER_V1_STANDARD:-0}

render_asset v1 ad-square-1080x1080.svg \
  yubios-ad-square-1080x1080.png yubios-ad-square-2160x2160.png \
  1080 1080 128 28 72 72 "$render_v1_standard"
render_asset v1 ad-landscape-1200x628.svg \
  yubios-ad-landscape-1200x628.png yubios-ad-landscape-2400x1256.png \
  1200 628 274 58 862 154 "$render_v1_standard"
render_asset v1 ad-medium-rectangle-300x250.svg \
  yubios-ad-medium-rectangle-300x250.png yubios-ad-medium-rectangle-600x500.png \
  300 250 48 11 18 17 "$render_v1_standard"
render_asset v1 ad-leaderboard-728x90.svg \
  yubios-ad-leaderboard-728x90.png yubios-ad-leaderboard-1456x180.png \
  728 90 64 14 14 13 "$render_v1_standard"
render_asset v1 ad-skyscraper-160x600.svg \
  yubios-ad-skyscraper-160x600.png yubios-ad-skyscraper-320x1200.png \
  160 600 88 21 36 30 "$render_v1_standard"
render_asset v1 ad-linux-penguin-banner-970x250.svg \
  yubios-ad-linux-penguin-banner-970x250.png yubios-ad-linux-penguin-banner-1940x500.png \
  970 250 66 15 28 22 "$render_v1_standard"

render_asset v2 ad-square-1080x1080.svg \
  yubios-ad-square-1080x1080.png yubios-ad-square-2160x2160.png \
  1080 1080 128 28 72 72 1
render_asset v2 ad-landscape-1200x628.svg \
  yubios-ad-landscape-1200x628.png yubios-ad-landscape-2400x1256.png \
  1200 628 64 14 54 48 1
render_asset v2 ad-medium-rectangle-300x250.svg \
  yubios-ad-medium-rectangle-300x250.png yubios-ad-medium-rectangle-600x500.png \
  300 250 48 11 18 17 1
render_asset v2 ad-leaderboard-728x90.svg \
  yubios-ad-leaderboard-728x90.png yubios-ad-leaderboard-1456x180.png \
  728 90 64 14 14 13 1
render_asset v2 ad-skyscraper-160x600.svg \
  yubios-ad-skyscraper-160x600.png yubios-ad-skyscraper-320x1200.png \
  160 600 88 21 36 30 1
render_asset v2 ad-linux-penguin-banner-970x250.svg \
  yubios-ad-linux-penguin-banner-970x250.png yubios-ad-linux-penguin-banner-1940x500.png \
  970 250 66 15 28 22 1

identify \
  "$ads_dir"/v1/*.png \
  "$ads_dir"/v2/*.png \
  "$ads_dir"/v1-upscaled/*.png \
  "$ads_dir"/v2-upscaled/*.png
