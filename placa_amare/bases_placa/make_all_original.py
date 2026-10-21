import sys, math
import numpy as np
import trimesh
from shapely.geometry import Polygon, box, LineString
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = sys.argv[1]
TILT, PLATE_T, CLEAR = 10.0, 3.0, 0.4
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
H1, D1, YT1, HB1, LEN1 = 15.0, 45.0, 33.0, 6.0, 120.0
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

# --- Base pequena 15 x 60 x 12,83 (mesma lógica, 2 peças por placa) ---
H2, D2, YT2, HB2, LEN2 = 12.83, 60.0, 42.0, 5.0, 15.0
sec2, pf2 = profile(D2, H2, YT2, HB2)
small = extrude(sec2, 0, LEN2)
assert small.is_watertight

# --- Montagem na mesa (256 x 256): grande atrás, duas pequenas na frente, espaçadas como as pontas da placa ---
scene = trimesh.Scene()
def place(mesh, name, x, y):
    T = np.eye(4); T[0, 3], T[1, 3] = x, y
    scene.add_geometry(mesh, node_name=name, geom_name=name, transform=T)
place(big, "Base_12cm_vazada", 68, 150)
place(small.copy(), "Base_pequena_1", 68, 60)
place(small.copy(), "Base_pequena_2", 68 + 120 - LEN2, 60)
scene.export(OUT + ".3mf")

ld = trimesh.load(OUT + ".3mf")
parts = list(ld.geometry.values()) if hasattr(ld, "geometry") else [ld]
print("objetos no 3MF:", len(parts), [(p.bounds[1] - p.bounds[0]).round(1).tolist() for p in parts])
print("volumes cm3: grande %.1f (%.0f g maciço) | pequena %.1f (%.0f g maciço) x2"
      % (big.volume/1000, big.volume/1000*1.24, small.volume/1000, small.volume/1000*1.24))

fig = plt.figure(figsize=(10, 5.2), dpi=130)
ax = fig.add_subplot(1, 2, 1)
ax.fill(*sec2.exterior.xy, color="#3a3f47")
pc0 = pf2 + n * (W / 2); h = PLATE_T / 2
pl = Polygon([pc0 - h*n, pc0 + h*n, pc0 + h*n + d*60, pc0 - h*n + d*60])
ax.fill(*pl.exterior.xy, color="#e8453c", alpha=0.6)
ax.set_aspect("equal"); ax.set_xlim(-3, 65); ax.set_ylim(-3, 70)
ax.set_title("Base pequena 15 x 60 mm (corte lateral)", fontsize=9)
ax.set_xlabel("profundidade Y (mm)  frente ← → trás"); ax.set_ylabel("altura Z (mm)")
ax2 = fig.add_subplot(1, 2, 2, projection="3d")
for name, g in scene.geometry.items():
    T = scene.graph.get(name)[0]
    vv = trimesh.transform_points(g.vertices, T)
    ax2.add_collection3d(Poly3DCollection(vv[g.faces], facecolor="#9aa3ad", edgecolor="#555", linewidths=0.1))
ax2.set_xlim(0, 256); ax2.set_ylim(0, 256); ax2.set_zlim(0, 256)
ax2.set_box_aspect((1, 1, 0.25)); ax2.view_init(elev=45, azim=-65)
ax2.set_title("Mesa de impressão (256 x 256 mm)", fontsize=10)
plt.tight_layout(); plt.savefig(OUT + "_previa.png")
