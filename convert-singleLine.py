from bs4 import BeautifulSoup
import unicodedata

# File paths
file_ref = "【参考】KST32B参照ファイル.svg"
file_font = "フォント.svg"
output_file = "converted_font.svg"

# --- Load files ---
with open(file_ref, "r", encoding="utf-8") as f:
    ref_content = f.read()
with open(file_font, "r", encoding="utf-8") as f:
    font_content = f.read()

# Parse with BeautifulSoup (XML mode for SVG)
soup_ref = BeautifulSoup(ref_content, "xml")
soup_font = BeautifulSoup(font_content, "xml")

# Build mapping: unicode → (glyph-name, horiz-adv-x)
glyph_map = {}
for glyph in soup_ref.find_all("glyph"):
    uni = glyph.get("unicode")
    if uni:
        uni_norm = unicodedata.normalize("NFKC", uni)
        glyph_map[uni_norm] = {
            "glyph-name": glyph.get("glyph-name"),
            "horiz-adv-x": glyph.get("horiz-adv-x", "500")
        }

# Convert <path> → <glyph>
new_glyphs = []
for path in soup_font.find_all("path"):
    label = path.get("inkscape:label")
    d_attr = path.get("d")

    if not label or not d_attr:
        continue

    # Normalize label for comparison
    label_norm = unicodedata.normalize("NFKC", label)

    if label_norm in glyph_map:
        # Create new <glyph>
        new_glyph = soup_font.new_tag("glyph")
        new_glyph["unicode"] = label_norm
        new_glyph["glyph-name"] = glyph_map[label_norm]["glyph-name"]
        new_glyph["horiz-adv-x"] = glyph_map[label_norm]["horiz-adv-x"]

        # Normalize path commands (lowercase → uppercase)
        d_normalized = d_attr.replace("m", "M").replace("l", "L").replace("c", "C")
        d_normalized = d_normalized.replace("q", "Q").replace("z", "Z")

        new_glyph["d"] = d_normalized
        new_glyphs.append(new_glyph)

# --- Build new SVG font ---
new_svg = BeautifulSoup("<svg><font></font></svg>", "xml")
font_tag = new_svg.find("font")

for g in new_glyphs:
    font_tag.append(g)

# Save result
with open(output_file, "w", encoding="utf-8") as f:
    f.write(str(new_svg))

print(f"✅ Conversion complete. Saved to: {output_file}")
