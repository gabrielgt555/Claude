import sys, zipfile
import numpy as np, cv2, mapbox_earcut as earcut
from shapely.geometry import Polygon

IMG, OUT = sys.argv[1], sys.argv[2]
BASE_H, RELIEF_H = float(sys.argv[3]), float(sys.argv[4])  # base branca + relevo vermelho (mm)
LARG_MM = float(sys.argv[6]) if len(sys.argv) > 6 else 100.0        # largura da imagem original = 100 mm (mesma escala ja impressa)
MARGEM_BAIXO = float(sys.argv[5]) if len(sys.argv) > 5 else 9.0  # faixa branca embaixo (fica dentro do suporte)
ESCALA_TEXTO = 0.92    # reducao de logo + C26 + A153
LAYER = 0.2

img = cv2.imread(IMG)
S = 4  # super-amostragem para bordas suaves
big = cv2.resize(img, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC).astype(np.int16)
h, w = big.shape[:2]
# "vermelhidao": ignora sombras cinzas e pega os brilhos rosados dentro das letras
red = cv2.GaussianBlur((big[:, :, 2] - np.maximum(big[:, :, 0], big[:, :, 1])).astype(np.float32), (0, 0), 2.0)
mask = (red > 35).astype(np.uint8) * 255
# preenche furinhos finos (reflexos de brilho); furos reais (detalhes do coracao) sao mais largos
inv = 255 - mask
n, lab, st, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
dist = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
for i in range(1, n):
    x, y, ww, hh, area = st[i]
    if x == 0 or y == 0 or x + ww >= w or y + hh >= h: continue  # fundo externo
    reg = lab[y:y+hh, x:x+ww] == i
    if dist[y:y+hh, x:x+ww][reg].max() < 11:
        mask[y:y+hh, x:x+ww][reg] = 255
mask = (cv2.GaussianBlur(mask, (0, 0), 3.0) > 127).astype(np.uint8) * 255
cv2.imwrite(OUT.replace('.3mf', '_mascara.png'), 255 - cv2.resize(mask, None, fx=1/S, fy=1/S, interpolation=cv2.INTER_AREA))

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

from shapely.geometry import box
from shapely import affinity
from shapely.ops import unary_union

K = LARG_MM / (w / S) / S      # mm por pixel (em super-amostragem)
cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
hier = hier[0]
def ring(c): return [(float(x), float(y)) for x, y in cv2.approxPolyDP(c, 1.6, True)[:, 0, :]]
polys = []
for i, c in enumerate(cnts):
    if hier[i][3] != -1 or cv2.contourArea(c) < 400: continue
    holes, k = [], hier[i][2]
    while k != -1:
        if cv2.contourArea(cnts[k]) >= 400: holes.append(ring(cnts[k]))
        k = hier[k][0]
    p = Polygon(ring(c), holes)
    if not p.is_valid: p = p.buffer(0)
    polys.append(p)

moldura = max(polys, key=lambda p: p.area)
xmin, ymin, xmax, ymax = moldura.bounds
ix0, iy0, ix1, iy1 = Polygon(moldura.interiors[0]).bounds   # area util dentro da moldura
resto = [p for p in polys if p is not moldura]
esq = [p for p in resto if p.centroid.x < 420 * S]            # AMARE + barra
dir_ = [p for p in resto if p.centroid.x >= 420 * S]           # logo + C26 + A153
bar_right = max(p.bounds[2] for p in esq)
gx0, gy0, gx1, gy1 = unary_union(dir_).bounds
alvo_cx, alvo_cy = (bar_right + ix1) / 2, (iy0 + iy1) / 2
cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
dir_ = [affinity.translate(affinity.scale(p, ESCALA_TEXTO, ESCALA_TEXTO, origin=(cx, cy)), alvo_cx - cx, alvo_cy - cy) for p in dir_]
relevo = [moldura] + esq + dir_

# base branca: contorno externo da moldura (sem borda) + faixa embaixo para encaixar no suporte
margem_px = MARGEM_BAIXO / K
base = unary_union([Polygon(moldura.exterior), box(xmin, ymax - 450, xmax, ymax + margem_px)])
Ytop = ymax + margem_px
def to_mm(g):
    return affinity.affine_transform(g, [K, 0, 0, -K, -xmin * K, Ytop * K])
rv, rt, bv, bt = [], [], [], []
for g_ in ([base] if base.geom_type == 'Polygon' else list(base.geoms)):
    extrude(to_mm(g_), 0, BASE_H, bv, bt)
for p in relevo:
    q = to_mm(p)
    for g_ in ([q] if q.geom_type == 'Polygon' else list(q.geoms)):
        extrude(g_, BASE_H, BASE_H + RELIEF_H, rv, rt)
W_MM, H_MM = (xmax - xmin) * K, (Ytop - ymin) * K
def mesh(V, T):
    vs = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V)
    ts = ''.join(f'<triangle v1="{a}" v2="{b_}" v3="{c}"/>' for a, b_, c in T)
    return f'<mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh>'
nome = f'Placa AMARE C26 A153 ({W_MM:.0f} mm)'
# um objeto com duas partes: base (filamento 1) e relevo (filamento 3)
model = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
 f'<metadata name="Title">{nome}</metadata><resources>'
 f'<object id="1" name="Base branca" type="model">{mesh(bv, bt)}</object>'
 f'<object id="2" name="Relevo vermelho" type="model">{mesh(rv, rt)}</object>'
 f'<object id="3" name="{nome}" type="model"><components><component objectid="1"/><component objectid="2"/></components></object>'
 '</resources><build>'
 f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128-W_MM/2} {128-H_MM/2} 0"/>'
 '</build></model>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print(OUT, f'{W_MM:.2f} x {H_MM:.2f} x {BASE_H+RELIEF_H:.1f} mm')
