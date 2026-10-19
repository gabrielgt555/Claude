"""Engorda os textos C26/A153 do projeto Bambu (extraido em DIR) para casar com a fonte original da placa.
uso: editar_texto_cheio.py DIR  (DIR = projeto 3MF ja extraido; altera 3D/Objects/object_1.model e Metadata/model_settings.config)"""
import sys, re, numpy as np, mapbox_earcut as earcut
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity

D = sys.argv[1].rstrip('/') + '/'
OFFSET, SX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45, float(sys.argv[3]) if len(sys.argv) > 3 else 1.08
Z0, Z1 = -0.115, 0.985            # embutido 0,1 na base e topo na altura do relevo
CX_ALVO = 72.55                   # centro do espaco livre entre a barra e a moldura
BASE_E = 17.8                     # base da letra E de AMARE (y, coord. do objeto)

src = open(D + '3D/Objects/object_1.model', encoding='utf-8').read()
cfg = open(D + 'Metadata/model_settings.config', encoding='utf-8').read()
vre = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>')

def objblock(s, oid):
    m = re.search(r'(<object id="%s"[^>]*>)(.*?)(</object>)' % oid, s, re.S); return m
def topo_poly(body):
    V = np.array([tuple(map(float, v)) for v in vre.findall(body)])
    T = np.array([tuple(map(int, t)) for t in re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"', body)])
    zt = V[:, 2].max()
    tris = [Polygon(V[t][:, :2]) for t in T if np.all(np.abs(V[t][:, 2] - zt) < 1e-4)]
    u = unary_union([t.buffer(1e-4) for t in tris]).buffer(-1e-4)
    return u

def engordar(u):
    geoms = sorted([g for g in (list(u.geoms) if u.geom_type == 'MultiPolygon' else [u]) if g.area > 1.0], key=lambda g: g.centroid.x)
    cx0 = unary_union(geoms).centroid.x
    gs = [g.buffer(OFFSET, join_style=2, mitre_limit=2.0) for g in geoms]
    gs = [affinity.scale(g, SX, 1.0, origin='center') for g in gs]
    for fator in np.arange(1.0, 1.4, 0.01):          # espaca as letras ate sobrar folga minima de 0,7 mm
        pos = [affinity.translate(g, (g.centroid.x - cx0) * (fator - 1), 0) for g in gs]
        gap = min(pos[i].distance(pos[i + 1]) for i in range(len(pos) - 1))
        if gap >= 0.7: break
    return pos, gap, fator

def extrude(poly, V, T):
    rings = [list(poly.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in poly.interiors]
    flat = np.array([p for r in rings for p in r], dtype=np.float64)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    idx = earcut.triangulate_float64(flat, ends).reshape(-1, 3)
    n, o = len(flat), len(V)
    for z in (Z0, Z1): V.extend((x, y, z) for x, y in flat)
    for a, b, c in idx:
        pa, pb, pc = flat[a], flat[b], flat[c]
        if (pb[0]-pa[0])*(pc[1]-pa[1]) - (pb[1]-pa[1])*(pc[0]-pa[0]) < 0: b, c = c, b
        T.append((o+a, o+c, o+b)); T.append((o+n+a, o+n+b, o+n+c))
    s = 0
    for r in rings:
        m = len(r)
        for i in range(m):
            p, q = s+i, s+(i+1) % m
            T.append((o+p, o+q, o+n+q)); T.append((o+p, o+n+q, o+n+p))
        s += m

info = {}
for oid, nome in (('3', 'C26'), ('4', 'A153')):
    m = objblock(src, oid)
    glifos, gap, fator = engordar(topo_poly(m.group(2)))
    U = unary_union(glifos)
    info[nome] = (glifos, U, gap, fator)

# posicao vertical: base da letra plana (A) do A153 na base do E; C26 com 1,4 mm de folga acima do A153
mat = {}
def origem(nome): 
    mm = re.search(r'name" value="%s"/>\s*<metadata key="matrix" value="([^"]+)"' % nome, cfg); return mm
g4, U4 = info['A153'][0], info['A153'][1]
a_base = g4[0].bounds[1]                                   # base do "A" (letra plana)
oy4 = BASE_E - a_base                                      # origem y do A153 (peca local y=0)
topo_a153 = oy4 + U4.bounds[3]
U3 = info['C26'][1]
oy3 = topo_a153 + 1.4 - U3.bounds[1]
ox3 = CX_ALVO - (U3.bounds[0] + U3.bounds[2]) / 2
ox4 = CX_ALVO - (U4.bounds[0] + U4.bounds[2]) / 2
NEW = {'C26': (ox3, oy3, info['C26']), 'A153': (ox4, oy4, info['A153'])}

for oid, nome in (('3', 'C26'), ('4', 'A153')):
    glifos = info[nome][0]
    V, T = [], []
    for g in glifos:
        for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)): extrude(p, V, T)
    vs = '\n'.join('     <vertex x="%.6f" y="%.6f" z="%.6f"/>' % v for v in V)
    ts = '\n'.join('     <triangle v1="%d" v2="%d" v3="%d"/>' % t for t in T)
    m = objblock(src, oid)
    body = m.group(2)
    body = re.sub(r'<vertices>.*?</vertices>', '<vertices>\n' + vs + '\n    </vertices>', body, flags=re.S)
    body = re.sub(r'<triangles>.*?</triangles>', '<triangles>\n' + ts + '\n    </triangles>', body, flags=re.S)
    src = src[:m.start(2)] + body + src[m.end(2):]
    NEW[nome] = NEW[nome] + (len(T),)
open(D + '3D/Objects/object_1.model', 'w', encoding='utf-8').write(src)

# posicoes nos metadados e no 3dmodel.model
mdl = open(D + '3D/3dmodel.model', encoding='utf-8').read()
for nome, oid in (('C26', '3'), ('A153', '4')):
    ox, oy, _, nt = NEW[nome]
    cfg = re.sub(r'(<metadata key="name" value="%s"/>\s*<metadata key="matrix" value=")[^"]*(")' % nome,
                 lambda m_: '%s1 0 0 %.6f 0 1 0 %.6f 0 0 1 1.6 0 0 0 1%s' % (m_.group(1), ox, oy, m_.group(2)), cfg)
    i = cfg.index('value="%s"/>' % nome); j = cfg.index('</part>', i)
    blk = re.sub(r'<mesh_stat face_count="\d+"', '<mesh_stat face_count="%d"' % (nt // 3), cfg[i:j])
    cfg = cfg[:i] + blk + cfg[j:]
    mdl = re.sub(r'(objectid="%s"[^>]*transform=")[^"]*(")' % oid,
                 lambda m_: '%s1 0 0 0 1 0 0 0 1 %.4f %.6f 1.6%s' % (m_.group(1), ox, oy, m_.group(2)), mdl)
open(D + '3D/3dmodel.model', 'w', encoding='utf-8').write(mdl)
open(D + 'Metadata/model_settings.config', 'w', encoding='utf-8').write(cfg)
for nome in ('C26', 'A153'):
    ox, oy, (gl, U, gap, fator), nt = NEW[nome]
    b = U.bounds
    print('%s: largura %.1f mm, altura %.1f mm, folga min entre letras %.2f mm (espacamento x%.2f)  centro X %.2f  y %.2f..%.2f' % (
        nome, b[2]-b[0], b[3]-b[1], gap, fator, ox + (b[0]+b[2])/2, oy + b[1], oy + b[3]))
