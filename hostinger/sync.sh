#!/bin/bash
# So What? → brandmizer.com. Run hourly by Hostinger cron. Copies site/<path>/ from the GitHub repo's main branch
# into public_html/<path>/, only if the new copy looks right. The old copy is kept one step back for rollback.
REPO="${SOWHAT_REPO:-OWNER/so-what}"   # set to the real GitHub repo, e.g. mourya/so-what
DEST="$HOME/domains/brandmizer.com/public_html"
LOG="$HOME/so-what-sync.log"
TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT
if ! curl -fsSL --max-time 60 "https://codeload.github.com/$REPO/tar.gz/refs/heads/main" -o "$TMP/r.tgz"; then
  echo "$(date -u +%FT%TZ) FAIL download $REPO" >> "$LOG"; exit 1; fi
tar -xzf "$TMP/r.tgz" -C "$TMP" || { echo "$(date -u +%FT%TZ) FAIL untar" >> "$LOG"; exit 1; }
SRC=$(ls -d "$TMP"/*/site/*/ 2>/dev/null | head -1); SRC="${SRC%/}"
NAME=$(basename "$SRC")
if [ -z "$SRC" ] || [ ! -s "$SRC/index.html" ] || ! grep -q "So <em>what?</em>" "$SRC/index.html"; then
  echo "$(date -u +%FT%TZ) FAIL no valid site/ in repo, live copy kept" >> "$LOG"; exit 1; fi
# unchanged? nothing to do
if [ -f "$DEST/$NAME/index.html" ] && cmp -s "$SRC/index.html" "$DEST/$NAME/index.html"; then exit 0; fi
rm -rf "$DEST/$NAME.new" "$DEST/$NAME.prev"
cp -R "$SRC" "$DEST/$NAME.new" && find "$DEST/$NAME.new" -type d -exec chmod 755 {} + && find "$DEST/$NAME.new" -type f -exec chmod 644 {} +
[ -d "$DEST/$NAME" ] && mv "$DEST/$NAME" "$DEST/$NAME.prev"
mv "$DEST/$NAME.new" "$DEST/$NAME"
STORIES=$(grep -o 'class="story"' "$DEST/$NAME/index.html" | wc -l | tr -d ' ')
UPDATED=$(grep -o 'Updated [^<]*' "$DEST/$NAME/index.html" | head -1)
NOTE=""; [ "$STORIES" -lt 3 ] && NOTE=" LOW-COUNT"
echo "$(date -u +%FT%TZ) OK $NAME stories=$STORIES $UPDATED$NOTE" >> "$LOG"
