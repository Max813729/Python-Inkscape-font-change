import xml.etree.ElementTree as ET

# Input files
font_file = "フォント.svg"
work_file = "作業ファイル.svg"
output_file = "converted.svg"

# Parse both SVG files
font_tree = ET.parse(font_file)
font_root = font_tree.getroot()

work_tree = ET.parse(work_file)
work_root = work_tree.getroot()

# SVG namespace fix
ns = {"svg": "http://www.w3.org/2000/svg"}
ET.register_namespace("", "http://www.w3.org/2000/svg")

# ---- Step 1: Extract style from 作業ファイル.svg ----
# We assume 作業ファイル has at least one <text> element with the desired style
work_text = work_root.find(".//svg:text", ns)
work_style = work_text.attrib.get("style", "")
work_attrib = {k: v for k, v in work_text.attrib.items() if k != "x" and k != "y"}

print("Reference style:", work_style)

# ---- Step 2: Apply this style to all text in フォント.svg ----
for text_elem in font_root.findall(".//svg:text", ns):
    # Overwrite style
    if work_style:
        text_elem.set("style", work_style)
    # Copy other attributes from reference text
    for k, v in work_attrib.items():
        if k not in ("x", "y", "style"):  # keep positions intact
            text_elem.set(k, v)

# ---- Step 3: Save as new SVG ----
font_tree.write(output_file, encoding="utf-8", xml_declaration=True)
print("Converted file saved as", output_file)
