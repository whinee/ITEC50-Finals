# Constants
SRC_DIR="./assets/static/images"
EXCLUDE_FOLDERS=("screenshots")
ICON_REL_SRC_PATH="lyra logo square.png"
ICON_REL_OUT_PATH="favicon.ico"
BANNER_REL_SRC_PATH="lyra logo.png"
BANNER_REL_OUT_PATH="banner.png"
WIDTHS=(24 48 96 144 256 320 480 720 1080 1440)

# Derived Variables
ICON_SRC_PATH="$SRC_DIR/$ICON_REL_SRC_PATH"
ICON_OUT_PATH="$SRC_DIR/$ICON_REL_OUT_PATH"
BANNER_SRC_PATH="$SRC_DIR/$BANNER_REL_SRC_PATH"
BANNER_OUT_PATH="$SRC_DIR/$BANNER_REL_OUT_PATH"

# Function to check if a path should be excluded
should_exclude() {
    local FILE="$1"
    for EX in "${EXCLUDE_FOLDERS[@]}"; do
        if [[ "$FILE" == *"/$EX/"* ]]; then
            return 0  # yes, exclude
        fi
    done
    return 1  # no, keep
}
magick "$ICON_SRC_PATH" -resize "180x180" -quality 80 "$ICON_OUT_PATH"
magick "$BANNER_SRC_PATH" -resize "1200x800" -quality 80 "$BANNER_OUT_PATH"

# find all images recursively
find "$SRC_DIR" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | while read IMG; do
    # skip excluded folders
    if should_exclude "$IMG"; then
        echo "Skipping $IMG"
        continue
    fi

    DIR_NAME="$(dirname "$IMG")"
    BASE_NAME="$(basename "$IMG" | sed 's/\.[^.]*$//')"  # strip extension

    for SIZE in "${WIDTHS[@]}"; do
        OUT_FILE="$DIR_NAME/${BASE_NAME}-${SIZE}w.webp"

        # convert + resize + optimize
        magick "$IMG" -resize "${SIZE}x" -quality 80 "$OUT_FILE"
        echo "Created $OUT_FILE"
    done
done

echo "All images optimized in-place!"