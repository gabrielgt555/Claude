import sys, re, zipfile
# uso: juntar_projeto.py placa.3mf base.3mf saida.3mf
PLACA, BASE, OUT = sys.argv[1:4]
GAP = 12.0
rd = lambda f: zipfile.ZipFile(f).read('3D/3dmodel.model').decode()
pm, sm = rd(PLACA), rd(BASE)
objs = re.findall(r'(<object id="(\d)".*?</object>)', pm, re.S)
base_o, rel_o, comp_o = [o for o, _ in objs]
stand = re.search(r'<mesh>.*?</mesh>', sm, re.S).group(0)
vs = [tuple(map(float, m)) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', base_o)]
W, H = max(v[0] for v in vs), max(v[1] for v in vs)
sv = [tuple(map(float, m)) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)"', stand)]
sw = max(v[0] for v in sv) - min(v[0] for v in sv); sd = max(v[1] for v in sv) - min(v[1] for v in sv)
scx = (max(v[0] for v in sv) + min(v[0] for v in sv)) / 2; scy = (max(v[1] for v in sv) + min(v[1] for v in sv)) / 2
D = H + GAP + sd; y0 = 128 - D / 2
assert D <= 250 and W <= 250 and sw <= 250, f'nao cabe na mesa: {W:.0f}x{D:.0f}'
plate_t = (128 - W / 2, y0 + sd + GAP)
stand_t = (128 - scx, y0 + sd / 2 - scy)
comp_o = comp_o.replace('id="3"', 'id="3"')
model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="pt-BR" '
 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
 + base_o + rel_o + comp_o +
 f'<object id="4" name="Base suporte" type="model">{stand}</object>'
 '</resources><build>'
 f'<item objectid="3" transform="1 0 0 0 1 0 0 0 1 {plate_t[0]:.3f} {plate_t[1]:.3f} 0"/>'
 f'<item objectid="4" transform="1 0 0 0 1 0 0 0 1 {stand_t[0]:.3f} {stand_t[1]:.3f} 0"/>'
 '</build></model>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', model)
print(OUT, f'placa {W:.0f}x{H:.0f} + base {sw:.0f}x{sd:.0f} | ocupa {max(W,sw):.0f}x{D:.0f} mm da mesa')
