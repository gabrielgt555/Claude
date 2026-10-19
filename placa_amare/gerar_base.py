import sys, zipfile, numpy as np, trimesh

# Medidas da placa (mm): padrao = placa reduzida a 47,62% (100 x 66,67 x 2,38)
PLACA_L = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
PLACA_E = float(sys.argv[2]) if len(sys.argv) > 2 else 2.4
OUT = sys.argv[3] if len(sys.argv) > 3 else 'base_suporte_placa.3mf'

FOLGA = 0.25               # folga por lado no encaixe
PAREDE_LAT = 8.0           # parede nas laterais
PROF = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0  # profundidade do encaixe
INCL = 10.0                # inclinacao para tras (graus)
BASE_P, BASE_A = 32.0, 16.0  # profundidade (Y) e altura (Z) do bloco

L = PLACA_L + 2 * FOLGA + 2 * PAREDE_LAT
bloco = trimesh.creation.box(extents=(L, BASE_P, BASE_A))
bloco.apply_translation((0, 0, BASE_A / 2))

fenda_l, fenda_e = PLACA_L + 2 * FOLGA, PLACA_E + 2 * FOLGA
fenda = trimesh.creation.box(extents=(fenda_l, fenda_e, PROF * 3))
fenda.apply_translation((0, 0, PROF * 1.5))                 # base da fenda em z=0
R = trimesh.transformations.rotation_matrix(np.radians(-INCL), (1, 0, 0))
fenda.apply_transform(R)                                     # topo inclina para tras (+Y)
fenda.apply_translation((0, -3.0, BASE_A - PROF))            # fundo do encaixe a PROF do topo

peca = bloco.difference(fenda, engine='manifold')
assert peca.is_watertight, 'malha nao fechada'

V, F = peca.vertices, peca.faces
V = V - [0, 0, V[:, 2].min()] + [128, 128, 0]
vs = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V)
ts = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F)
model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" '
 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
 f'<object id="1" name="Base suporte placa" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>'
 '</resources><build><item objectid="1"/></build></model>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print(OUT, 'dim', np.round(peca.extents, 2), 'vol', round(peca.volume), 'mm3', 'tris', len(F))
