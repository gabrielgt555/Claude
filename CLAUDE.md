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

## Regra para gerar/editar arquivos .3mf (Bambu Studio)
- O Bambu Studio pode descartar os ajustes globais gravados em `Metadata/project_settings.config` e carregar o perfil de fábrica no lugar (visto no projeto dos retirantes). **Não confiar só no global.**
- Em todo .3mf gerado ou editado, gravar as configurações importantes **dentro de cada objeto** (`Metadata/model_settings.config`, metadados do `<object>`): altura da camada, loops de parede, gerador de paredes (arachne), detecção de paredes finas, preenchimento (densidade e padrão), camadas de topo, velocidades de parede, brim e suportes.
- Além disso, manter o global coerente e listar as chaves alteradas em `different_settings_to_system` (índice 0 = processo, 1 = impressora, depois um por filamento).
- Ao terminar, **reabrir o arquivo gerado e conferir** (script) objeto por objeto, e entregar ao usuário uma tabela curta com o que ficou gravado, para ele não precisar conferir tudo no programa. Dizer claramente que não foi aberto no Bambu Studio.
- Malhas vindas de gerador de imagem para 3D podem trazer pintura multicolor (`paint_color` nos triângulos) que ativa troca de cor e torre de limpeza: remover quando o pedido for uma cor só.
- Usar chaves válidas do Bambu (por exemplo `zig-zag` para o padrão "Retilíneo" do engomar) e ids únicos de objeto e de UUID ao juntar projetos.
