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

- Oito texturas 2D de 64x64 para grama, terra, asfalto, areia, agua, musgo,
  ruinas e lama, com variacoes automáticas para reduzir repeticao visual.
- Arvores cartunescas baseadas em `tree.png` e `RedTree.png`, renderizadas sem animacao.
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
- `core/context.py`: concentra os servicos compartilhados pelas cenas.
- `core/state_manager.py`: registra rotas e controla a pilha de cenas e overlays.
- `assets/data/`: define itens, entidades e armas em JSON validado pelo `ContentCatalog`.
- `assets/sprites/`: pixel arts 2D de armas e itens em 64x64.
- `graphics/particles.py`: particulas ambientais e feedback de combate.
- `graphics/ambience.py`: coloracao de bioma e faixas de nevoa 2D.
- `states/`: telas isoladas que dependem apenas do contexto e das rotas.
- `components/`: regras reutilizaveis de fisica, combate, status, sprite e inventario.
- `entities/`: composicao dos componentes em entidades do jogo.
- `map/`: grid, biomas e geracao procedural do mundo.
- `graphics/`: carregamento de recursos e renderizacao.

## Adicionar conteudo

Itens novos entram em `assets/data/items.json`, armas em `assets/data/weapons.json`
e inimigos em `assets/data/entities.json`. Referencias sao validadas ao iniciar o jogo;
um nome de item inexistente produz um erro explicito.

## Adicionar uma cena

1. Crie uma classe que herde de `BaseState` em `states/`.
2. Adicione sua rota ao enum `Scene`.
3. Registre a classe em `GameApplication._register_scenes()`.
4. Navegue com `manager.push(...)` para overlays ou `manager.change(...)` para troca total.

Overlays devem declarar `transparent = True`. Apenas a cena no topo recebe update e
input, enquanto o gerenciador desenha automaticamente as cenas visiveis abaixo dela.
