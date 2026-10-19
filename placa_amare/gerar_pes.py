import sys, re, zipfile, numpy as np, trimesh

# uso: gerar_pes.py placa_AMS.3mf saida.3mf esp_placa larg_pe prof_pe esp_base alt_parede esp_parede
PLACA, OUT = sys.argv[1], sys.argv[2]
ESP_PLACA, LARG, PROF, T, ALT, TP = map(float, sys.argv[3:9])
INCL, FOLGA, MARG_FRENTE, GAP = 10.0, 0.25, 10.0, 8.0
G = ESP_PLACA + 2 * FOLGA            # abertura do encaixe

# perfil lateral (como no desenho): barra longa na base + 2 paredes finas inclinadas 10 graus para tras
def parede(offset):
    b = trimesh.creation.box(extents=(LARG, TP, ALT + 3))          # 3 mm enterrados na base
    b.apply_translation((0, offset, (ALT - 3) / 2))
    return b
paredes = [parede(-(G / 2 + TP / 2)), parede(G / 2 + TP / 2)]
rot = trimesh.transformations.rotation_matrix(np.radians(-INCL), (1, 0, 0))
yc = MARG_FRENTE + TP + G / 2
paredes = [p.apply_transform(rot).apply_translation((0, yc, T)) for p in paredes]
barra = trimesh.creation.box(extents=(LARG, PROF, T)); barra.apply_translation((0, PROF / 2, T / 2))
pe = trimesh.boolean.union([barra] + paredes, engine='manifold')
assert pe.is_watertight
pe.apply_translation(-pe.bounds[0])
V, F = pe.vertices, pe.faces
foot = '<mesh><vertices>' + ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V) + '</vertices><triangles>' + ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F) + '</triangles></mesh>'
fw, fd = pe.extents[0], pe.extents[1]

pm = zipfile.ZipFile(PLACA).read('3D/3dmodel.model').decode()
base_o, rel_o, comp_o = [o for o, _ in re.findall(r'(<object id="(\d)".*?</object>)', pm, re.S)]
vs = [tuple(map(float, m)) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)"', base_o)]
W, H = max(v[0] for v in vs), max(v[1] for v in vs)
D = H + GAP + fd; y0 = 128 - D / 2
assert D <= 252 and W <= 250, f'nao cabe na mesa: {W:.0f} x {D:.0f}'
gap_pes = 10.0
x0 = 128 - (2 * fw + gap_pes) / 2
items = (f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128 - W/2:.3f} {y0 + fd + GAP:.3f} 0"/>'
         f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0:.3f} {y0:.3f} 0"/>'
         f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0 + fw + gap_pes:.3f} {y0:.3f} 0"/>')
model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
         + base_o + rel_o + comp_o + f'<object id="4" name="Pe suporte (imprimir 2)" type="model">{foot}</object>'
         + '</resources><build>' + items + '</build></model>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print(f'{OUT}: placa {W:.0f}x{H:.0f} | pe {fw:.0f}x{fd:.0f}x{pe.extents[2]:.0f} mm (x2) vol {pe.volume*2/1000:.0f} cm3 | mesa {max(W,2*fw+gap_pes):.0f}x{D:.0f}')
