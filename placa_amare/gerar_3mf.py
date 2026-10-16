import sys, zipfile
import numpy as np, cv2, mapbox_earcut as earcut
from shapely.geometry import Polygon

IMG, OUT = sys.argv[1], sys.argv[2]
W_MM, H_MM = 210.0, 150.0   # 21 x 15 cm
BASE_H, RELIEF_H = 2.0, 2.0  # base branca + relevo vermelho 2 mm

img = cv2.imread(IMG)
h, w = img.shape[:2]
b, g, r = [img[:, :, i].astype(int) for i in range(3)]
mask = ((r - np.maximum(g, b) > 70) & (r > 110)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
mask = (cv2.GaussianBlur(mask,(0,0),2.0) > 127).astype(np.uint8)*255
cv2.imwrite(OUT.replace('.3mf', '_mascara.png'), 255 - mask)

sx, sy = W_MM / w, H_MM / h
cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
hier = hier[0]
def pts(c):
    c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :]
    return [(x * sx, (h - y) * sy) for x, y in c]  # y invertido (imagem -> mesa)

verts, tris = [], []
def add_box(x0, y0, x1, y1, z0, z1):
    o = len(verts)
    for z in (z0, z1):
        verts.extend([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
    for a, b_, c in [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]:
        tris.append((o+a, o+b_, o+c))

def extrude(poly, z0, z1, V, T):
    rings = [list(poly.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in poly.interiors]
    flat = np.array([p for r_ in rings for p in r_], dtype=np.float64)
    ends = np.cumsum([len(r_) for r_ in rings]).astype(np.uint32)
    idx = earcut.triangulate_float64(flat, ends).reshape(-1, 3)
    n, o = len(flat), len(V)
    for z in (z0, z1):
        V.extend((x, y, z) for x, y in flat)
    for a, b_, c in idx:
        # base de baixo (invertida) e topo
        pa, pb, pc = flat[a], flat[b_], flat[c]
        cr = (pb[0]-pa[0])*(pc[1]-pa[1]) - (pb[1]-pa[1])*(pc[0]-pa[0])
        if cr < 0: b_, c = c, b_
        T.append((o+a, o+c, o+b_))          # fundo
        T.append((o+n+a, o+n+b_, o+n+c))    # topo
    s = 0
    for r_ in rings:
        m = len(r_)
        for i in range(m):
            p, q = s+i, s+(i+1) % m
            T.append((o+p, o+q, o+n+q)); T.append((o+p, o+n+q, o+n+p))
        s += m

# polígonos (externo + furos) -> shapely, garantindo orientação correta
rv, rt = [], []
for i, c in enumerate(cnts):
    if hier[i][3] != -1 or cv2.contourArea(c) < 12: continue
    ext = Polygon(pts(c))
    holes = []
    k = hier[i][2]
    while k != -1:
        if cv2.contourArea(cnts[k]) >= 60: holes.append(pts(cnts[k]))
        k = hier[k][0]
    p = Polygon(ext.exterior.coords, holes)
    if not p.is_valid: p = p.buffer(0)
    for g_ in ([p] if p.geom_type == 'Polygon' else list(p.geoms)):
        extrude(g_, BASE_H, BASE_H + RELIEF_H, rv, rt)

add_box(0, 0, W_MM, H_MM, 0, BASE_H)

# relevo desloca-se de volta para sobre a base: mesh sem sobreposição (base z0-2, relevo z2-4)
def mesh_xml(V, T, pid, oid, name):
    vs = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V)
    ts = ''.join(f'<triangle v1="{a}" v2="{b_}" v3="{c}"/>' for a, b_, c in T)
    return (f'<object id="{oid}" name="{name}" type="model" pid="1" pindex="{pid}"><mesh>'
            f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')

# ajuste: a base é a caixa; tris/verts globais referem-se só à caixa
model = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
 '<metadata name="Title">Placa AMARE C26 A153</metadata><resources>'
 '<basematerials id="1"><base name="Branco" displaycolor="#FFFFFF"/><base name="Vermelho" displaycolor="#E00000"/></basematerials>'
 + mesh_xml(verts, tris, 0, 2, 'Base branca')
 + mesh_xml(rv, rt, 1, 3, 'Relevo vermelho 2mm')
 + '</resources><build>'
 f'<item objectid="2" transform="1 0 0 0 1 0 0 0 1 {128-W_MM/2} {128-H_MM/2} 0"/>'
 f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128-W_MM/2} {128-H_MM/2} 0"/>'
 '</build></model>')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print('contornos:', len(cnts), 'vertices relevo:', len(rv), 'tris relevo:', len(rt))
