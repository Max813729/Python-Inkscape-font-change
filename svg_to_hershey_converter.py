from bs4 import BeautifulSoup
import re
import statistics

# File paths
file_ref = "2-参照用ファイル.svg"      # Source with paths
file_template = "1-作業ファイル.svg"  # Template with desired style
file_output = "converted_fixed_size.svg"

# Load SVGs
with open(file_ref, "r", encoding="utf-8") as f:
    soup_ref = BeautifulSoup(f, "xml")
with open(file_template, "r", encoding="utf-8") as f:
    soup_template = BeautifulSoup(f, "xml")

# --- Helper functions ---
def parse_translate_xy(transform_text: str):
    """Extract x,y from translate(x,y)"""
    if not transform_text:
        return None
    m = re.search(r"translate\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)", transform_text)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))

def update_css_prop(style_str: str, prop: str, new_value: str):
    """Update or add a CSS property inside a style string"""
    parts = [p.strip() for p in style_str.split(";") if p.strip()]
    for i, p in enumerate(parts):
        if p.lower().startswith(prop.lower() + ":"):
            parts[i] = f"{prop}:{new_value}"
            break
    else:
        parts.append(f"{prop}:{new_value}")
    return ";".join(parts)

def get_font_size_px(style_str: str, default_px: float = 3.175):
    """Extract font-size in px from style string"""
    m = re.search(r"font-size\s*:\s*([\d.]+)\s*px", style_str, flags=re.I)
    return float(m.group(1)) if m else default_px

# --- Extract style from template ---
sample_text_tag = soup_template.find("text")
sample_style = sample_text_tag.get(
    "style", "font-size:3.175px;fill:#000000;stroke:none"
) if sample_text_tag else "font-size:3.175px;fill:#000000;stroke:none"
template_font_px = get_font_size_px(sample_style)

# Template line spacing (median Δy)
template_y_vals = sorted({
    float(t.get("y", "0")) for t in soup_template.find_all("text") if t.get("y")
})
template_line_dy = statistics.median(
    [abs(b - a) for a, b in zip(template_y_vals, template_y_vals[1:])]
) if len(template_y_vals) >= 2 else None

# --- Extract characters from reference ---
paths = soup_ref.find_all("path", attrs={"inkscape:label": True})
char_data = []
for p in paths:
    char = p["inkscape:label"]
    xy = parse_translate_xy(p.get("transform", ""))
    if xy is None:
        continue
    x, y = xy
    char_data.append({"char": char, "x": x, "y": y})

# Group into rows by Y (tolerance)
row_tolerance = 2.0
rows = {}
for item in char_data:
    y = item["y"]
    row_key = None
    for key in rows.keys():
        if abs(key - y) <= row_tolerance:
            row_key = key
            break
    if row_key is None:
        row_key = y
        rows[row_key] = []
    rows[row_key].append(item)

sorted_rows = sorted(rows.items(), key=lambda r: r[0])
for y, chars in sorted_rows:
    chars.sort(key=lambda c: c["x"])

# Reference line spacing (median Δy)
ref_row_keys = [rk for rk, _ in sorted_rows]
ref_line_dy = statistics.median(
    [abs(b - a) for a, b in zip(ref_row_keys, ref_row_keys[1:])]
) if len(ref_row_keys) >= 2 else None

# --- Determine scaling factor ---
scale = 1.0
if template_line_dy and ref_line_dy and template_line_dy > 0:
    scale = ref_line_dy / template_line_dy

# Apply scale to font size
new_font_px = template_font_px * scale
new_style = update_css_prop(sample_style, "font-size", f"{new_font_px:.6f}px")

# --- Build new SVG using template root ---
svg_root_template = soup_template.find("svg")
new_svg = BeautifulSoup(features="xml")
svg_tag = new_svg.new_tag("svg", **svg_root_template.attrs)
new_svg.append(svg_tag)

# Copy <defs> from template
defs_tag = soup_template.find("defs")
if defs_tag:
    svg_tag.append(BeautifulSoup(str(defs_tag), "xml"))

# Add text rows
for y, chars in sorted_rows:
    text_tag = new_svg.new_tag("text", x="0", y=str(-y), style=new_style)
    tspan_tag = new_svg.new_tag("tspan", x="0", y=str(-y))
    tspan_tag.string = "".join(c["char"] for c in chars)
    text_tag.append(tspan_tag)
    svg_tag.append(text_tag)

# Save
with open(file_output, "w", encoding="utf-8") as f:
    f.write(new_svg.prettify())

print(f"Saved converted file: {file_output}")
