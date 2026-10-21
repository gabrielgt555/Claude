import sys, math
import numpy as np
import trimesh
from shapely.geometry import Polygon, box, LineString
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = sys.argv[1]
TILT, PLATE_T, CLEAR = 10.0, 1.6, 0.4   # PLATE_T = faixa branca (1,6 mm) que entra no encaixe
W = PLATE_T + CLEAR
FLOOR, TIP = 3.0, 0.8
t = math.radians(TILT); s = -1       # inclinada para a frente
d = np.array([s * math.sin(t), math.cos(t)])
n = np.array([math.cos(t), -s * math.sin(t)])


def profile(depth, H, y_top, hb):
    zf = FLOOR - min(0.0, W * n[1])
    yf = y_top - (H - zf) * s * math.tan(t)
    pf = np.array([yf, zf]); pb = pf + W * n
    yb = pb[0] + (hb - pb[1]) * s * math.tan(t)
    sec = Polygon([(0, 0), (depth, 0), (depth, hb), (yb, hb), tuple(pb), tuple(pf), (y_top, H), (0, TIP)])
    assert sec.is_valid and yb < depth - 4
    return sec, pf


def extrude(poly, x0, x1):
    m = trimesh.creation.extrude_polygon(poly, x1 - x0)
    v = m.vertices[:, [2, 0, 1]].copy(); v[:, 0] += x0
    mm = trimesh.Trimesh(vertices=v, faces=m.faces, process=True)
    trimesh.repair.fix_normals(mm)
    return mm


# --- Base grande 120 x 45 x 15, vazada ---
H1, D1, YT1, HB1, LEN1 = 13.5, 45.0, 33.0, 6.0, 120.0   # altura 13,5: o labio nao esconde a moldura (faixa de 10,8 mm)
sec1, pf1 = profile(D1, H1, YT1, HB1)
slope = (H1 - TIP) / YT1
pk = []
for (y0, y1) in [(12.0, 19.0), (21.0, 26.0), (28.0, 31.2)]:
    p = box(y0, 1.2, y1, TIP + slope * y0 - 2.2); pk.append(p)
    assert sec1.buffer(-1.15).contains(p)
    assert p.distance(LineString([tuple(pf1), (YT1, H1)])) >= 2.4
big = extrude(sec1, 0, LEN1)
for p in pk:
    big = trimesh.boolean.difference([big, extrude(p, 2.0, LEN1 - 2.0)], engine="manifold")
assert big.is_watertight

# --- Base pequena: pe ORIGINAL 25 x 100 x 21,39 (o mesmo do projeto da placa), 2 pecas por placa ---
import zipfile, re
_x = zipfile.ZipFile(sys.argv[2]).read("3D/3dmodel.model").decode()
_o = re.findall(r'<object id="4".*?</object>', _x, re.S)[0]
_V = np.array([tuple(map(float, m)) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', _o)])
_T = np.array([tuple(map(int, m)) for m in re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"', _o)])
small = trimesh.Trimesh(_V - _V.min(0), _T, process=True); trimesh.repair.fix_normals(small)
LEN2 = float(small.extents[0]); assert small.is_watertight
sec2 = Polygon([(0, 0), (1, 0), (1, 1)]); pf2 = np.array([0.0, 0.0])

# --- Montagem na mesa (256 x 256): grande atrás, duas pequenas na frente, espaçadas como as pontas da placa ---
scene = trimesh.Scene()
def place(mesh, name, x, y):
    T = np.eye(4); T[0, 3], T[1, 3] = x, y
    scene.add_geometry(mesh, node_name=name, geom_name=name, transform=T)
place(big, "Base_12cm_vazada", 68, 170)
place(small.copy(), "Pe_25x100_1", 68, 45)
place(small.copy(), "Pe_25x100_2", 68 + 120 - LEN2, 45)
scene.export(OUT + ".3mf")

ld = trimesh.load(OUT + ".3mf")
parts = list(ld.geometry.values()) if hasattr(ld, "geometry") else [ld]
print("objetos no 3MF:", len(parts), [(p.bounds[1] - p.bounds[0]).round(1).tolist() for p in parts])
print("volumes cm3: grande %.1f | pe %.1f x2" % (big.volume/1000, small.volume/1000))

fig = plt.figure(figsize=(7, 5), dpi=130)
ax2 = fig.add_subplot(1, 1, 1, projection="3d")
for name, g in scene.geometry.items():
    T = scene.graph.get(name)[0]
    vv = trimesh.transform_points(g.vertices, T)
    ax2.add_collection3d(Poly3DCollection(vv[g.faces], facecolor="#9aa3ad", edgecolor="#555", linewidths=0.1))
ax2.set_xlim(0, 256); ax2.set_ylim(0, 256); ax2.set_zlim(0, 256)
ax2.set_box_aspect((1, 1, 0.25)); ax2.view_init(elev=45, azim=-65)
ax2.set_title("Mesa de impressao (256 x 256 mm)", fontsize=10)
plt.tight_layout(); plt.savefig(OUT + "_previa.png")
