# Rogue Llama

Roguelike em Pygame com mundo procedural, combate, inventario e sobrevivencia.

## Controles

- `WASD` ou setas: movimento.
- Mouse esquerdo: usar a arma 2D equipada.
- Mouse direito: ataque corpo a corpo rapido.
- `1`, `2`, `3`, `4`: pistola, escopeta, SMG e facao.
- `R`: recarregar.
- `I` ou `Tab`: inventario.
- `Esc` ou `P`: pausar.
- `F3`: mostrar ou ocultar hitboxes e tiles bloqueados.

## Arsenal e itens

- Pistola M9: equilibrada, carregador de 12 tiros.
- Escopeta Tatica: seis projeteis por disparo e alto espalhamento.
- SMG de Sucata: automatica, desbloqueada como loot dos Runners.
- Facao Reforcado: ataque corpo a corpo de maior alcance.
- Energetico: aumenta temporariamente a velocidade de movimento.
- Colete Tatico: adiciona armadura que absorve dano antes do HP.
- Municao 9mm e cartuchos calibre 12 usam reservas separadas.

As armas e os itens usam sprites 2D transparentes de exatamente 64x64 em
`assets/sprites/`. Os efeitos sonoros de tiro, recarga, coleta, impacto e ataque
corpo a corpo sao sintetizados localmente pelo `SoundManager`.

## Mundo e ambientacao

- Um grande deserto procedural reutiliza a textura de areia existente, com formato
  irregular; caminhos de terra podem atravessar a região e passos levantam poeira.
- Jogador, esqueleto e orcs usam animações `idle/run` do Pixel Crawler Free Pack,
  ampliadas em escala inteira e alinhadas ao grid de 32x32.
- Grama, terra, água, lama, neve, pedras e sete variações de árvores usam os
  atlas de natureza do Pixel Crawler; as árvores adultas vêm das folhas Size_04
  nativas e todos os elementos mantêm escala inteira e pixels nítidos.
- Bosques são formados em grupos e abrem clareiras conectadas por trilhas
  orgânicas. Hortas cercadas e acampamentos com fogueira funcionam como pequenos
  pontos de interesse e deixam corredores livres para o jogador.
- As demais clareiras recebem vilarejos determinísticos com três casas completas,
  lotes desobstruídos, fundações sólidas e acessos ligados à praça central.
- Lagoas são posicionadas em áreas verdes, usam as margens animadas do atlas e
  recebem juncos e flores. Rotas que cruzam água viram pontes de madeira.
- A antiga área azul virou uma região de neve com árvores congeladas, pinheiros,
  pedras sem quadrados de grama e cristais raros.
- As pedras bloqueadas são desenhadas sobre a grama, sem quadrados transparentes;
  o deserto preserva a textura de areia que já existia no projeto.
- Florestas, ruínas, neve e desertos distribuem em densidades diferentes arbustos,
  plantas, capim, flores, cogumelos, folhas, galhos, tocos, minerais e pedras.
- Folhas ao vento, poeira de passos, nevoa, brilhos de coleta e particulas de impacto.
- Coloracao ambiental por terreno, nevoa movel, vento continuo e passaros ocasionais.
- O grid visual de debug fica desligado durante o jogo normal.

## Executar

Requer Python 3.10 ou superior.

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

Para rodar os testes:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Arquitetura

- `core/application.py`: inicializa o Pygame, monta as dependencias e executa o loop.
- `core/context.py`: concentra servicos injetados e o estado global explicito da sessao.
- `states/base_state.py`: define o contrato das cenas sem criar ciclo com o gerenciador.
- `core/state_manager.py`: registra rotas e controla a pilha de cenas e overlays.
- `assets/data/`: define itens, entidades e armas em JSON validado pelo `ContentCatalog`.
- `assets/sprites/`: pixel arts 2D de armas e itens em 64x64.
- `assets/sprites/pixel_crawler/`: personagens e atlas de natureza de Anokolisa,
  acompanhados da licença original.
- `graphics/particles.py`: particulas ambientais e feedback de combate.
- `graphics/ambience.py`: coloracao de bioma e faixas de nevoa 2D.
- `graphics/lighting.py`: escuridao e luzes com gradientes reutilizados em cache.
- `states/`: telas isoladas que dependem apenas do contexto e das rotas.
- `components/`: regras reutilizaveis de fisica, combate, impacto, status, sprite e inventario.
- `entities/`: composicao dos componentes em entidades do jogo.
- `map/settings.py`: configuracao validada das dimensoes e da populacao do mundo.
- `map/terrain_generation.py`, `map/roads.py` e `map/composicao.py`: etapas isoladas da geracao procedural.
- `map/simulation.py`: atualizacao de entidades, projeteis, drops, efeitos e particulas.
- `map/terrain.py`: fonte unica para colisao e materiais de tiles e decoracoes.
- `map/map_gen.py`: orquestra as etapas acima usando uma seed e RNGs injetados.
- `graphics/`: carregamento de recursos e renderizacao.

A mesma seed produz o mesmo terreno, pontos de interesse e entidades. Decisoes de
gameplay usam um RNG separado, evitando que efeitos visuais alterem a geracao. Assets
sao procurados no projeto, no diretorio instalado ou no caminho definido por
`ROGUE_LLAMA_ASSETS`.

## Adicionar conteudo

Itens novos entram em `assets/data/items.json`, armas em `assets/data/weapons.json`
e entidades em `assets/data/entities.json`. Entidades declaram `role`, `tags`,
`impact_material` e comportamento de IA nos dados; regras de jogo nao devem depender
do nome exibido. Referencias, tipos, slots, materiais e limites numericos sao validados
ao iniciar o jogo, produzindo um erro explicito quando o conteudo e inconsistente.

## Adicionar uma cena

1. Crie uma classe que herde de `BaseState` em `states/`.
2. Adicione sua rota ao enum `Scene`.
3. Registre a classe em `GameApplication._register_scenes()`.
4. Navegue com `manager.push(...)` para overlays ou `manager.change(...)` para troca total.

Overlays devem declarar `transparent = True`. Apenas a cena no topo recebe update e
input, enquanto o gerenciador desenha automaticamente as cenas visiveis abaixo dela.
