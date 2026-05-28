set -euo pipefail

# Constants
SRC_DIR="./src/static/assets/images"
PAPER_DIR="./paper"

ICON_IMG_REL_SRC_PATH="light-favicon.svg"
DARK_ICON_PDF_REL_SRC_PATH="dark-favicon-not-safe.svg"
LIGHT_ICON_PDF_REL_SRC_PATH="light-favicon-not-safe.svg"
DARK_ICON_REL_PDF_OUT_PATH="dark-logo.pdf"
LIGHT_ICON_REL_PDF_OUT_PATH="light-logo.pdf"
ICON_REL_IMG_OUT_PATH="favicon.ico"
ICON_REL_BIG_IMG_OUT_PATH="logo.png"

# BANNER_REL_SRC_PATH="lyra banner.png"
# BANNER_REL_OUT_PATH="banner.png"

WIDTHS=(24 48 96 144 256 320 480 720 1080 1440)

# Derived Variables
ICON_IMG_SRC_PATH="$SRC_DIR/$ICON_IMG_REL_SRC_PATH"
DARK_ICON_PDF_SRC_PATH="$SRC_DIR/$DARK_ICON_PDF_REL_SRC_PATH"
LIGHT_ICON_PDF_SRC_PATH="$SRC_DIR/$LIGHT_ICON_PDF_REL_SRC_PATH"
DARK_ICON_PDF_OUT_PATH="$PAPER_DIR/$DARK_ICON_REL_PDF_OUT_PATH"
LIGHT_ICON_PDF_OUT_PATH="$PAPER_DIR/$LIGHT_ICON_REL_PDF_OUT_PATH"
ICON_IMG_OUT_PATH="$SRC_DIR/$ICON_REL_IMG_OUT_PATH"
ICON_BIG_IMG_OUT_PATH="$SRC_DIR/$ICON_REL_BIG_IMG_OUT_PATH"
# BANNER_SRC_PATH="$SRC_DIR/$BANNER_REL_SRC_PATH"
# BANNER_OUT_PATH="$SRC_DIR/$BANNER_REL_OUT_PATH"

EXCLUDE_FOLDERS=("screenshots")
EXCLUDE_FILES=(
    "$ICON_IMG_SRC_PATH"
	# "$BANNER_SRC_PATH"
	# "$BANNER_OUT_PATH"
	"$SRC_DIR/bg.png"
)

cairosvg "$DARK_ICON_PDF_SRC_PATH" -o "$DARK_ICON_PDF_OUT_PATH"
cairosvg "$LIGHT_ICON_PDF_SRC_PATH" -o "$LIGHT_ICON_PDF_OUT_PATH"
# inkscape "$DARK_ICON_PDF_SRC_PATH" --export-area-drawing --export-filename="$DARK_ICON_PDF_OUT_PATH"
# inkscape "$LIGHT_ICON_PDF_SRC_PATH" --export-area-drawing --export-filename="$LIGHT_ICON_PDF_OUT_PATH"
magick "$ICON_IMG_SRC_PATH" -resize "180x180" -strip -quality 80 "$ICON_IMG_OUT_PATH"
cairosvg "$ICON_IMG_SRC_PATH" -o "$ICON_BIG_IMG_OUT_PATH" --output-width 10000
# magick "$BANNER_SRC_PATH" -resize "1200x800" -strip -quality 80 "$BANNER_OUT_PATH"

# Function to check if a path should be excluded
should_exclude() {
    local FILE="$1"

    # exclude folders
    for EX in "${EXCLUDE_FOLDERS[@]}"; do
        if [[ "$FILE" == *"/$EX/"* ]]; then
            return 0
        fi
    done

    # exclude files
    for EX in "${EXCLUDE_FILES[@]}"; do
        if [[ "$(basename "$FILE")" == "$EX" ]]; then
            return 0
        fi
    done

    return 1
}

# find all images recursively
find "$SRC_DIR" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | while read IMG; do
    # skip excluded folders
    if should_exclude "$IMG"; then
        echo "Skipping $IMG"
        continue
    fi

    DIR_NAME="$(dirname "$IMG")"
    BASE_NAME="$(basename "$IMG" | sed 's/\.[^.]*$//')"  # strip extension

    ORIG_WIDTH=$(magick identify -format "%w" "$IMG")

	for SIZE in "${WIDTHS[@]}"; do
		# skip if target size is larger than original
		if (( SIZE > ORIG_WIDTH )); then
			echo "Skipping ${SIZE}w for $IMG (original: ${ORIG_WIDTH}px)"
			continue
		fi

		OUT_FILE="$DIR_NAME/${BASE_NAME}-${SIZE}w.webp"

		# convert + resize + optimize
		magick "$IMG" -resize "${SIZE}x" -strip -quality 80 -define webp:method=6 -define webp:auto-filter=true -define webp:lossless=false "$OUT_FILE"

		echo "Created $OUT_FILE"
	done
done

echo "All images optimized in-place!"