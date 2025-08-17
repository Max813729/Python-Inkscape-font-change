from bs4 import BeautifulSoup
import re
import statistics

# File paths
file_ref = "test-1.svg"        # Source with paths
file_template = "example.svg"  # Template with desired style
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

# --- Extract characters from reference in document order ---
paths = soup_ref.find_all("path", attrs={"inkscape:label": True})
char_data = []
for p in paths:  # preserves document order
    char = p["inkscape:label"]
    xy = parse_translate_xy(p.get("transform", ""))
    if xy is None:
        continue
    x, y = xy
    char_data.append({"char": char, "x": x, "y": y})

# If no characters found, stop
if not char_data:
    raise RuntimeError("No characters found in reference file.")

# --- Compute reference line Y (all characters are on one line) ---
ref_y_vals = [c["y"] for c in char_data]
avg_y = statistics.mean(ref_y_vals)

# --- Extract fill color from reference ---
ref_fill = None
for p in paths:
    style = p.get("style", "")
    m = re.search(r"fill\s*:\s*(#[0-9a-fA-F]{3,6})", style)
    if m:
        ref_fill = m.group(1)
        break
if not ref_fill:
    ref_fill = "#000000"  # fallback default

# --- Font size scaling ---
# Since all characters are on one line, just keep template font size
new_font_px = template_font_px
new_style = update_css_prop(sample_style, "font-size", f"{new_font_px:.6f}px")
new_style = update_css_prop(new_style, "fill", ref_fill)

# --- Build new SVG using template root ---
svg_root_template = soup_template.find("svg")
new_svg = BeautifulSoup(features="xml")
svg_tag = new_svg.new_tag("svg", **svg_root_template.attrs)
new_svg.append(svg_tag)

# Copy <defs> from template
defs_tag = soup_template.find("defs")
if defs_tag:
    svg_tag.append(BeautifulSoup(str(defs_tag), "xml"))

# --- Normalize Y to fit inside template viewBox ---
baseline_template_y = float(sample_text_tag.get("y", "0")) if sample_text_tag else 0.0
y_offset = baseline_template_y - avg_y
new_y = avg_y + y_offset

# --- Add a single text element with all characters ---
text_tag = new_svg.new_tag("text", x="0", y=str(new_y), style=new_style)
tspan_tag = new_svg.new_tag("tspan", x="0", y=str(new_y))
tspan_tag.string = "".join(c["char"] for c in char_data)  # preserve doc order
text_tag.append(tspan_tag)
svg_tag.append(text_tag)

# Save
with open(file_output, "w", encoding="utf-8") as f:
    f.write(new_svg.prettify())

print(f"Saved converted file: {file_output}")
