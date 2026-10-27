# Preferências do usuário (impressão 3D)

## Impressora
- Bambu Lab A1 com AMS Lite. Bico **0,4 mm padrão** da A1, sem nenhuma modificação física. Mesa PEI texturizada.
- Filamentos usuais: PLA (branco, preto, vermelho; também amarelo/dourado e outros).

## Regra de alerta de bico
- Sempre que um projeto, perfil ou arquivo (.3mf, .gcode.3mf) usar **bico menor que 0,4 mm** (por exemplo, "A1 0.2 nozzle", larguras de linha ~0,22 mm), **avisar o usuário antes de dar qualquer configuração**: o perfil não corresponde à impressora dele e ele precisa trocar para "Bambu Lab A1 0.4 nozzle".
- Dar as recomendações de velocidade, camada e largura de linha sempre para o bico de 0,4 mm.

## Formato das explicações de configuração (Bambu Studio)
- Para cada mudança: **Onde** (aba, grupo e nome da opção), **Como está**, **Como fica** e **Por quê** (com o efeito colateral).
- Indicar quando a opção só aparece com o botão Avançado ligado ou está em outra aba que a esperada.
