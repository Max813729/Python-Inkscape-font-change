import xml.etree.ElementTree as ET
from pathlib import Path
from svgpathtools import parse_path

# --- File paths ---
font_path = Path("フォント.svg")        # input file
out_path  = Path("フォント_converted.svg")  # output file

# --- Namespaces ---
NS = {
    "svg": "http://www.w3.org/2000/svg",
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix if prefix != "svg" else "", uri)

def parse(svg_path: Path) -> ET.ElementTree:
    return ET.parse(str(svg_path))

def path_bbox(d):
    """Return bounding box (xmin, ymin, xmax, ymax) of an SVG path string."""
    path = parse_path(d)
    xs = [seg.start.real for seg in path] + [seg.end.real for seg in path]
    ys = [seg.start.imag for seg in path] + [seg.end.imag for seg in path]
    return min(xs), min(ys), max(xs), max(ys)

def make_text_from_path(path_elem: ET.Element) -> ET.Element:
    """Convert <path inkscape:label=...> to <text><tspan><tspan>."""
    label = path_elem.attrib.get(f"{{{NS['inkscape']}}}label", "")
    if not label:
        return None

    d = path_elem.attrib.get("d", "")
    try:
        xmin, ymin, xmax, ymax = path_bbox(d)
        x = str((xmin + xmax) / 2)   # center X
        y = str((ymin + ymax) / 2)   # center Y
        font_size = str(ymax - ymin)   # match height of path
    except Exception:
        x, y, font_size = "0", "0", "16"   # fallback if path is broken

    # Create <text>
    text_elem = ET.Element(f"{{{NS['svg']}}}text", {
        "xml:space": "preserve",
        "x": x,
        "y": y,
        "style": f"font-size:{font_size}px;fill:#000000;stroke:none",
        "fill": "#000000",
        "stroke": "none",
    })

    # Outer tspan (positioning)
    tspan1 = ET.SubElement(text_elem, f"{{{NS['svg']}}}tspan", {
        "x": x, "y": y
    })
    # Inner tspan (actual text content)
    tspan2 = ET.SubElement(tspan1, f"{{{NS['svg']}}}tspan")
    tspan2.text = label

    return text_elem

# --- Load SVG ---
font_tree = parse(font_path)
font_root = font_tree.getroot()

# --- Replace paths with texts ---
for parent in font_root.findall(".//svg:g", NS) + [font_root]:
    for path in list(parent.findall("svg:path", NS)):
        new_text = make_text_from_path(path)
        if new_text is not None:
            parent.insert(list(parent).index(path), new_text)
        parent.remove(path)

# --- Save result ---
font_tree.write(out_path, encoding="utf-8", xml_declaration=True)
print("Converted file saved as:", out_path)
