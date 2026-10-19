import sys, re, zipfile, numpy as np, trimesh

# uso: gerar_pes.py placa_AMS.3mf saida.3mf esp_placa larg_pe prof_pe esp_base alt_parede esp_parede
PLACA, OUT = sys.argv[1], sys.argv[2]
ESP_PLACA, LARG, PROF, T, ALT, TP = map(float, sys.argv[3:9])
TF = float(sys.argv[9]) if len(sys.argv) > 9 else T            # espessura reforcada sob o encaixe
MARG_FRENTE = float(sys.argv[10]) if len(sys.argv) > 10 else 10.0  # recuo do encaixe em relacao a frente do pe
INCL, FOLGA, GAP = 10.0, 0.20, 8.0
G = ESP_PLACA + 2 * FOLGA            # abertura do encaixe

# perfil lateral (como no desenho): barra longa na base + 2 paredes finas inclinadas 10 graus para tras
def parede(offset):
    b = trimesh.creation.box(extents=(LARG, TP, ALT + 3))          # 3 mm enterrados na base
    b.apply_translation((0, offset, (ALT - 3) / 2))
    return b
paredes = [parede(-(G / 2 + TP / 2)), parede(G / 2 + TP / 2)]
rot = trimesh.transformations.rotation_matrix(np.radians(-INCL), (1, 0, 0))
yc = MARG_FRENTE + TP + G / 2
paredes = [p.apply_transform(rot).apply_translation((0, yc, TF)) for p in paredes]
# perfil lateral da barra: bloco grosso (TF) sob o encaixe + rampa descendo ate a espessura T no fundo
y_flat = yc + G / 2 + TP + 8.0
y_ramp = min(PROF, y_flat + (TF - T) * 2.5)
perfil = [(0, 0), (PROF, 0), (PROF, T), (y_ramp, T), (y_flat, TF), (0, TF)] if TF > T else [(0, 0), (PROF, 0), (PROF, T), (0, T)]
from shapely.geometry import Polygon
barra = trimesh.creation.extrude_polygon(Polygon(perfil), height=LARG)      # (u=y, v=z, w=x)
barra.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
barra.apply_translation((-LARG / 2, 0, 0))
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
gap_pes = 10.0
girar = H + GAP + fd > 252          # pe comprido demais para ficar na frente da placa: deita 90 graus, um atras do outro
if girar:
    D = H + GAP + 2 * fw + 5; y0 = 128 - D / 2
    assert D <= 252 and W <= 250 and fd <= 250, f'nao cabe na mesa: {W:.0f} x {D:.0f}'
    xs = 128 - fd / 2 + fd
    items = (f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128 - W/2:.3f} {y0 + 2*fw + 5 + GAP:.3f} 0"/>'
             f'<item objectid="4" transform="0 1 0 -1 0 0 0 0 1 {xs:.3f} {y0:.3f} 0"/>'
             f'<item objectid="4" transform="0 1 0 -1 0 0 0 0 1 {xs:.3f} {y0 + fw + 5:.3f} 0"/>')
else:
    D = H + GAP + fd; y0 = 128 - D / 2
    assert D <= 252 and W <= 250, f'nao cabe na mesa: {W:.0f} x {D:.0f}'
    x0 = 128 - (2 * fw + gap_pes) / 2
    items = (f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128 - W/2:.3f} {y0 + fd + GAP:.3f} 0"/>'
             f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0:.3f} {y0:.3f} 0"/>'
             f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0 + fw + gap_pes:.3f} {y0:.3f} 0"/>')
model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
         + base_o + rel_o + comp_o + f'<object id="4" name="Pe suporte (imprimir 2)" type="model">{foot}</object>'
         + '</resources><build>' + items + '</build></model>')
DUAS = len(sys.argv) > 11 and sys.argv[11] == 'duas_placas'
if DUAS:   # placa na Placa 1 e pes na Placa 2 (a Placa 2 fica ao lado: passo = 1,2 x largura da mesa)
    PASSO = 256 * 1.2
    x0 = 128 + PASSO - (2 * fw + gap_pes) / 2; yb = 128 - fd / 2
    items = (f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {128 - W/2:.3f} {128 - H/2:.3f} 0"/>'
             f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0:.3f} {yb:.3f} 0"/>'
             f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0 + fw + gap_pes:.3f} {yb:.3f} 0"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             + base_o + rel_o + comp_o + f'<object id="4" name="Pe suporte (imprimir 2)" type="model">{foot}</object>'
             + '</resources><build>' + items + '</build></model>')
SO_PES = len(sys.argv) > 11 and sys.argv[11] == 'so_pes'
if SO_PES:   # projeto so com os dois pes (impressao em placa separada, cor unica)
    x0 = 128 - (2 * fw + gap_pes) / 2; yb = 128 - fd / 2
    items = (f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0:.3f} {yb:.3f} 0"/>'
             f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {x0 + fw + gap_pes:.3f} {yb:.3f} 0"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             + f'<object id="4" name="Pe suporte (imprimir 2)" type="model">{foot}</object>' + '</resources><build>' + items + '</build></model>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print(f'{OUT}: placa {W:.0f}x{H:.0f} | pe {fw:.0f}x{fd:.0f}x{pe.extents[2]:.0f} mm (x2) vol {pe.volume*2/1000:.0f} cm3 | mesa {W:.0f}x{D:.0f}{' (pes deitados)' if girar else ''}')
