# Projeto Bases + Placa 12 cm (atualizado com as medidas reais)

Arquivo: Projeto_Bases_Placa_corrigido.3mf (3 objetos, abre no Bambu Studio)
Gerador: make_all.py  ->  python3 make_all.py <saida_sem_extensao> <3mf_com_o_pe_25x100>
(o 3mf do pe é gerado por ../gerar_pes.py; a malha do objeto 4 é usada como pe)
Dependências: pip install trimesh shapely mapbox-earcut manifold3d lxml matplotlib numpy networkx

## Pendências resolvidas
- Espessura que entra no encaixe: **1,6 mm** (faixa branca da base), NÃO 3 mm. O relevo (1,0 mm) fica acima do encaixe. Placa inteira = 2,6 mm.
- Altura da placa: **88,62 mm** (120 x 88,62; moldura de 120 x 77,82; faixa branca de baixo de 10,8 mm).
- Pé original 25 x 100 x 21,39 mm (encaixe 2,1 mm, 10 graus): usado no lugar da base pequena escalada.

## Mudanças em relação ao primeiro resumo
- Base grande: encaixe de 3,4 para **2,0 mm** (1,6 + 0,4 de folga). Altura de 15 para **13,5 mm** para o lábio frontal
  (10,7 mm ao longo da placa) não cobrir a moldura vermelha (a faixa branca tem 10,8 mm).
- Base pequena 15 x 60 substituída pelo **pé 25 x 100** (2 peças). Lábio do pé: 10 mm < 10,8 mm, ok.
- Montagem na mesa refeita (a grande em y=170, pés em y=45..145) porque o pé de 100 mm sobrepunha a base grande.

## Impressão (Bambu Studio, A1)
- Pés/bases: preenchimento 20% (pés de 25 x 100), 3 paredes, camada 0,24 mm.
- Placa: engomar só no branco, fluxo do vermelho 0,99, parede externa 0,30-0,35, superfície superior 0,38.
- Preto Velvet: bico 215-220 C, mesa Textured PEI 55 C, vel. volumétrica máx. 18 mm3/s
