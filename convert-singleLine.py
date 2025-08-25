# -*- coding: utf-8 -*-
"""
Build SVG font for Inkscape Hershey Text:
 - Glyph-names matched to reference when Unicode matches
 - Each glyph keeps its own stroked path (not overwritten with AAA pattern)
 - Size/position preserved via transform application
 - Font-family = 「その他のSVGフォント」
"""

import re
import xml.etree.ElementTree as ET
from collections import defaultdict

REF_FILE = "【参考】KST32B参照ファイル.svg"
SRC_FILE = "フォント.svg"
OUT_FILE = "その他のSVGフォント_fixed.svg"

# ----------------- Path utilities -----------------
_token_re = re.compile(
    r"[MmZzLlHhVvCcSsQqTtAa]|"
    r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
)

def _parse_path(d):
    tokens = _token_re.findall(d)
    i = 0
    while i < len(tokens):
        cmd = tokens[i]; i += 1
        if cmd in "Mm": nargs = 2
        elif cmd in "Ll": nargs = 2
        elif cmd in "Hh": nargs = 1
        elif cmd in "Vv": nargs = 1
        elif cmd in "Cc": nargs = 6
        elif cmd in "Ss": nargs = 4
        elif cmd in "Qq": nargs = 4
        elif cmd in "Tt": nargs = 2
        elif cmd in "Aa": nargs = 7
        elif cmd in "Zz":
            yield (cmd, []); continue
        else: break
        params = []
        while i < len(tokens) and not re.match(r"^[MmZzLlHhVvCcSsQqTtAa]$", tokens[i]):
            params.append(float(tokens[i])); i += 1
        for j in range(0, len(params), nargs):
            if len(params[j:j+nargs]) < nargs: break
            yield (cmd, params[j:j+nargs])

def _transform_path(d, a,b,c,d_m,e,f):
    def fmt(x): s=f"{x:.6f}".rstrip("0").rstrip("."); return "0" if s=="-0" else s
    out=[]
    def XY(x,y,absf): return (a*x+c*y+(e if absf else 0), b*x+d_m*y+(f if absf else 0))
    for cmd,params in _parse_path(d):
        absf=cmd.isupper()
        if cmd in "MmLlTt":
            x,y=params; x2,y2=XY(x,y,absf)
            out.append(cmd+f" {fmt(x2)} {fmt(y2)}")
        elif cmd in "Hh":
            x=params[0]; x2=a*x+(e if absf else 0)
            out.append(cmd+f" {fmt(x2)}")
        elif cmd in "Vv":
            y=params[0]; y2=d_m*y+(f if absf else 0)
            out.append(cmd+f" {fmt(y2)}")
        elif cmd in "CcSsQq":
            pts=[]
            for k in range(0,len(params),2):
                x2,y2=XY(params[k],params[k+1],absf); pts+=[fmt(x2),fmt(y2)]
            out.append(cmd+" "+" ".join(pts))
        elif cmd in "Aa":
            rx,ry,rot,large,sweep,x,y=params
            x2,y2=XY(x,y,absf); rx2,ry2=abs(a)*rx,abs(d_m)*ry
            out.append(cmd+" "+" ".join([
                fmt(rx2),fmt(ry2),fmt(rot),str(int(large)),str(int(sweep)),fmt(x2),fmt(y2)]))
        elif cmd in "Zz": out.append(cmd)
    return " ".join(out)

def _parse_matrix(s):
    m=re.findall(r"matrix\(\s*([^)]+)\)", s or "")
    if not m: return None
    vals=[float(x) for x in re.split(r"[ ,]+", m[0].strip()) if x]
    return vals if len(vals)==6 else None

# ----------------- Step 1: Reference font mapping -----------------
NS={"svg":"http://www.w3.org/2000/svg"}
ref_tree=ET.parse(REF_FILE); ref_root=ref_tree.getroot()
ref_font=ref_root.find(".//svg:font",NS)
default_adv=ref_font.attrib.get("horiz-adv-x") if ref_font is not None else "1000"
ref_face=ref_root.find(".//svg:font-face",NS)
face_metrics={"units-per-em":"1000","ascent":"800","descent":"-200"}
if ref_face is not None:
    for k in face_metrics:
        if k in ref_face.attrib: face_metrics[k]=ref_face.attrib[k]
unicode_to_name={}; unicode_to_adv={}
for g in ref_root.findall(".//svg:glyph",NS):
    u=g.attrib.get("unicode")
    if not u: continue
    if "glyph-name" in g.attrib: unicode_to_name[u]=g.attrib["glyph-name"]
    if "horiz-adv-x" in g.attrib: unicode_to_adv[u]=g.attrib["horiz-adv-x"]

# ----------------- Step 2: Source font paths -----------------
NS_ALL={"svg":"http://www.w3.org/2000/svg","ink":"http://www.inkscape.org/namespaces/inkscape"}
font_tree=ET.parse(SRC_FILE); font_root=font_tree.getroot()
group_transform_for_path={}
for g in font_root.findall(".//svg:g",NS_ALL):
    mat=_parse_matrix(g.attrib.get("transform"))
    if not mat: continue
    for p in g.findall(".//svg:path",NS_ALL):
        group_transform_for_path[id(p)]=mat
paths_by_unicode=defaultdict(list)
for p in font_root.findall(".//svg:path",NS_ALL):
    label=p.attrib.get("{http://www.inkscape.org/namespaces/inkscape}label")
    if not label: continue
    u=label[0]; paths_by_unicode[u].append(p)

# ----------------- Step 3: Build output font -----------------
out_svg=ET.Element("svg",{"xmlns":"http://www.w3.org/2000/svg","version":"1.1"})
defs=ET.SubElement(out_svg,"defs")
out_font=ET.SubElement(defs,"font",{"id":"KST32B","horiz-adv-x":default_adv})
ET.SubElement(out_font,"font-face",{
    "font-family":"その他のSVGフォント",
    "units-per-em":face_metrics["units-per-em"],
    "ascent":face_metrics["ascent"],
    "descent":face_metrics["descent"],
})
ET.SubElement(out_font,"missing-glyph",{"horiz-adv-x":default_adv})

created=0; matched=0; auto_named=0
for u,plist in sorted(paths_by_unicode.items(),key=lambda kv: kv[0]):
    glyph_name=unicode_to_name.get(u)
    adv=unicode_to_adv.get(u,default_adv)
    if not glyph_name:
        code=ord(u)
        glyph_name="SPACE" if code==0x20 else f"uni{code:04X}"
        auto_named+=1
    else:
        matched+=1

    # Merge path data for this glyph, applying group transform if present
    ds=[]
    for p in plist:
        d=p.attrib.get("d"); 
        if not d: continue
        mat=group_transform_for_path.get(id(p))
        if mat: d=_transform_path(d,*mat)
        ds.append(d)
    full_d=" ".join(ds)

    ET.SubElement(out_font,"glyph",{
        "unicode":u,"glyph-name":glyph_name,"horiz-adv-x":adv,"d":full_d
    })
    created+=1

ET.ElementTree(out_svg).write(OUT_FILE,encoding="utf-8",xml_declaration=True)
print("Output:",OUT_FILE)
print("Glyphs created:",created,"Matched:",matched,"Auto-named:",auto_named)
