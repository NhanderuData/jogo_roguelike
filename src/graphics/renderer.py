# src/graphics/renderer.py
import pygame
from core import config
from graphics import recursos
from graphics import shaders
from graphics.ambience import AmbientRenderer
from graphics.lighting import LightingRenderer
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)
        
        self.lighting = LightingRenderer(
            (config.LARGURA_TELA, config.ALTURA_TELA)
        )
        self.ambience = AmbientRenderer()
        self._shared_shadow_cache = {}

    @staticmethod
    def _linha_de_profundidade(world_y, camera_y=0.0):
        """Retorna a linha de contato com o chão em coordenadas de tela.

        ``x/y`` das entidades e dos elementos de tile identificam o tile onde
        seus pés/base estão apoiados. Ordenar pela origem desse tile introduz
        um atraso de 32 px: o personagem só vinha para frente do objeto depois
        de atravessar uma linha inteira. A borda inferior é a referência comum
        correta para ambos.
        """
        return (world_y + 1.0) * config.TAMANHO_TILE - camera_y

    # --- CORREÇÃO AQUI: Substituímos Rotação por SKEW (Cisalhamento) ---
    def gerar_sombra_realista(self, sprite_img, escala_tamanho=1.0):
        if not sprite_img: return None
        
        # 1. Cria a silhueta preta (Mask)
        try:
            mask = pygame.mask.from_surface(sprite_img)
            sombra_surf = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        except (pygame.error, ValueError, TypeError):
            return None

        # 2. Achata a sombra verticalmente (Escala Y)
        # 0.5 significa que a sombra terá metade da altura do objeto original
        w, h = sombra_surf.get_size()
        novo_h = int(h * 0.5 * escala_tamanho) 
        sombra_surf = pygame.transform.scale(sombra_surf, (w, novo_h))

        # 3. Aplica o Efeito SKEW (Inclina linha por linha)
        # Fator de inclinação (quanto maior, mais "deitada" a sombra para o lado)
        skew_factor = 0.6 
        offset_total = int(novo_h * skew_factor)
        largura_final = w + abs(offset_total)
        
        surface_final = pygame.Surface((largura_final, novo_h), pygame.SRCALPHA)
        
        # Loop "Pixel Perfect": Desloca cada linha de pixels para a direita
        # A linha de baixo (base) desloca 0. A linha de cima desloca o máximo.
        # Isso garante que a BASE continue no mesmo lugar!
        for i in range(novo_h):
            # Invertemos o i para que a base (y alto) tenha shift 0
            shift = int((novo_h - i) * skew_factor)
            
            # Pega uma linha da imagem achatada
            linha = sombra_surf.subsurface((0, i, w, 1))
            
            # Cola na nova superfície com o deslocamento
            surface_final.blit(linha, (shift, i))
            
        return surface_final

    def _render_scene(self, surface, mapa_obj, cor_noite=(0, 0, 0, 0)):
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y
        # O atlas original possui quatro frames de 100 ms.
        water_animation_frame = pygame.time.get_ticks() // 100
        
        # --- 1. RENDER QUEUE (Camadas) ---
        render_queue = []
        # Decorações são ancoradas pelo centro inferior do tile. Casas e cercas
        # largas podem continuar visíveis mesmo quando a âncora já saiu alguns
        # tiles da tela, portanto o culling precisa considerar esse volume.
        margem_colunas = 4
        margem_inferior = 7
        start_col = max(0, int(cam_x // config.TAMANHO_TILE) - margem_colunas)
        end_col = min(
            mapa_obj.largura,
            int((cam_x + surface.get_width()) // config.TAMANHO_TILE)
            + margem_colunas
            + 1,
        )
        start_row = max(0, int(cam_y // config.TAMANHO_TILE) - 1)
        end_row = min(
            mapa_obj.altura,
            int((cam_y + surface.get_height()) // config.TAMANHO_TILE)
            + margem_inferior
            + 1,
        )

        # Tiles
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = mapa_obj.obter_tile(x, y)
                if not tile: continue
                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                depth_y = self._linha_de_profundidade(y, cam_y)
                
                img_key = "terrain_grass"
                if tile.tipo == "rocha":
                    img_key = {
                        "neve": "terrain_moss",
                        "ruinas": "terrain_rubble",
                        "deserto": "terrain_sand",
                    }.get(getattr(tile, "bioma", None), "terrain_grass")
                elif tile.tipo == "parede": img_key = "wall"
                elif tile.tipo in ("terra", "terrain_dirt"): img_key = "terrain_dirt"
                elif tile.tipo == "grass": img_key = "terrain_grass"
                elif tile.tipo == "blue_ground": img_key = "terrain_moss"
                elif tile.tipo == "estrada": img_key = "terrain_road"
                elif tile.tipo == "deep_water": img_key = "terrain_water"
                elif tile.tipo == "sand": img_key = "terrain_sand"
                elif tile.tipo == "coast": img_key = "terrain_coast"
                elif tile.tipo == "rubble": img_key = "terrain_rubble"
                elif tile.tipo == "mud": img_key = "terrain_mud"
                elif tile.tipo == "bridge":
                    orientacao = getattr(tile, "orientacao", None) or "vertical"
                    img_key = f"terrain_bridge_{orientacao}"

                pond_edge_frames = None
                if tile.tipo == "deep_water" and tile.bioma == "lagoa":
                    edge_name = self._pond_edge_name(mapa_obj, x, y)
                    if edge_name:
                        pond_edge_frames = recursos.SPRITES.get(
                            f"terrain_pond_edge_{edge_name}_frames"
                        )

                variants = recursos.SPRITES.get(f"{img_key}_variants")
                if pond_edge_frames:
                    img = pond_edge_frames[
                        water_animation_frame % len(pond_edge_frames)
                    ]
                elif variants:
                    if tile.tipo == "deep_water":
                        phase = (x // 5) * 3 + (y // 5) * 5
                        variation = (water_animation_frame + phase) % len(variants)
                    else:
                        variation = (x * 31 + y * 17) % len(variants)
                    img = variants[variation]
                else:
                    variation = (x * 31 + y * 17) % 3
                    if variation == 1 and f"{img_key}_flip_x" in recursos.SPRITES:
                        img_key = f"{img_key}_flip_x"
                    elif variation == 2 and f"{img_key}_flip_y" in recursos.SPRITES:
                        img_key = f"{img_key}_flip_y"
                    img = recursos.SPRITES.get(img_key)
                if img: 
                    render_queue.append((config.LAYER_CHAO, screen_y, img, screen_x, screen_y))

                if tile.tipo == "rocha":
                    rock_key = "rock_brown" if (x * 13 + y * 7) % 3 == 0 else "rock"
                    rock = recursos.SPRITES.get(rock_key)
                    if rock:
                        rock_x = screen_x + (config.TAMANHO_TILE - rock.get_width()) // 2
                        rock_y = screen_y + config.TAMANHO_TILE - rock.get_height()
                        render_queue.append((
                            config.LAYER_CORPO,
                            depth_y,
                            rock,
                            rock_x,
                            rock_y,
                        ))
                
                self.adicionar_transicoes(
                    mapa_obj, tile.tipo, x, y, screen_x, screen_y, render_queue
                )

                decoration_key = getattr(tile, "decoracao", None)
                decoration_frames = recursos.SPRITES.get(
                    f"{decoration_key}_frames"
                )
                if decoration_frames:
                    decoration = decoration_frames[
                        water_animation_frame % len(decoration_frames)
                    ]
                else:
                    decoration = recursos.SPRITES.get(decoration_key)
                if decoration:
                    decoration_x = screen_x + (
                        config.TAMANHO_TILE - decoration.get_width()
                    ) // 2
                    decoration_y = (
                        screen_y + config.TAMANHO_TILE - decoration.get_height()
                    )
                    layer = (
                        config.LAYER_CORPO
                        if decoration_key in recursos.DECORACOES_ALTAS
                        else config.LAYER_DECORACAO
                    )
                    render_queue.append((
                        layer,
                        depth_y,
                        decoration,
                        decoration_x,
                        decoration_y,
                    ))

        # Entidades próximas da câmera. A margem superior inclui copas grandes.
        view_rect = pygame.Rect(
            int(cam_x) - 320,
            int(cam_y) - 384,
            surface.get_width() + 640,
            surface.get_height() + 768,
        )
        if hasattr(mapa_obj, "nearby_entities"):
            visible_entities = list(mapa_obj.nearby_entities(view_rect))
        else:
            visible_entities = mapa_obj.entidades

        for ent in visible_entities:
            if not hasattr(ent, 'sprite') or not ent.sprite.image: continue
            
            physics = ent.physics
            sprite = ent.sprite
            screen_x = physics.x * config.TAMANHO_TILE - cam_x
            screen_y = physics.y * config.TAMANHO_TILE - cam_y
            entity_depth_y = self._linha_de_profundidade(physics.y, cam_y)
            
            img_w = sprite.image.get_width()
            img_h = sprite.image.get_height()
            
            # Posição onde o SPRITE será desenhado
            draw_x = screen_x + (config.TAMANHO_TILE // 2) - (img_w // 2) + sprite.offset_x
            draw_y = screen_y + config.TAMANHO_TILE - img_h + sprite.offset_y

            # Árvores 3x são grandes; descarte entidades totalmente fora da tela
            # antes de gerar suas sombras para manter o custo proporcional à visão.
            render_margin = 48
            if (
                draw_x + img_w < -render_margin
                or draw_x > surface.get_width() + render_margin
                or draw_y + img_h < -render_margin
                or draw_y > surface.get_height() + render_margin
            ):
                continue

            # --- Sombra (CORRIGIDO) ---
            # Só desenha sombra se não for Layer de chão e tiver escala configurada
            if sprite.scale_sombra > 0:
                if not sprite.sombra_cache:
                    cache_key = (id(sprite.image), sprite.scale_sombra)
                    sprite.sombra_cache = self._shared_shadow_cache.get(cache_key)
                    if not sprite.sombra_cache:
                        sprite.sombra_cache = self.gerar_sombra_realista(
                            sprite.image, sprite.scale_sombra
                        )
                        self._shared_shadow_cache[cache_key] = sprite.sombra_cache
                
                if sprite.sombra_cache:
                    sombra = sprite.sombra_cache
                    s_h = sombra.get_height()
                    
                    # ALINHAMENTO:
                    # Como usamos Skew na base (shift=0 na base), o X da sombra é igual ao X do sprite.
                    # O Y da sombra deve alinhar o "pé" da sombra com o "pé" do sprite.
                    
                    sombra_x = draw_x 
                    # "Pé" do sprite = draw_y + img_h
                    # Queremos que "Pé" da sombra (sombra_y + s_h) seja igual a pé do sprite
                    sombra_y = (draw_y + img_h) - s_h - 2 # -2 pixels para subir um pouquinho e não vazar
                    
                    render_queue.append((
                        config.LAYER_SOMBRA,
                        entity_depth_y,
                        sombra,
                        sombra_x,
                        sombra_y,
                    ))

            # Corpo
            img_final = sprite.image
            if hasattr(sprite, 'dano_timer') and sprite.dano_timer > 0:
                img_hit = shaders.aplicar_flash_branco(sprite.image)
                if img_hit: img_final = img_hit
            render_queue.append((
                sprite.layer,
                entity_depth_y,
                img_final,
                draw_x,
                draw_y,
            ))

        # Projéteis
        for p in mapa_obj.projeteis:
            if p.image and p.active:
                px = p.x * config.TAMANHO_TILE - cam_x
                py = p.y * config.TAMANHO_TILE - cam_y
                rect = p.image.get_rect(center=(px, py))
                render_queue.append((config.LAYER_AEREO, py, p.image, rect.x, rect.y))

        # Desenhar Camadas
        render_queue.sort(key=lambda item: (item[0], item[1]))
        for _, _, img, x, y in render_queue:
            surface.blit(img, (x, y))

        mapa_obj.particulas.draw(surface, cam_x, cam_y)

        # --- 2. ESCURIDÃO AMBIENTAL (Subtractive) ---
        if cor_noite[3] > 0:
            self.lighting.apply_darkness(surface, cor_noite)


        # --- 3. LUZES ADITIVAS / GLOW (Additive) ---
        self.lighting.draw_lights(surface, mapa_obj, cam_x, cam_y)

        self.ambience.draw(surface, mapa_obj)

        # Pós-Processamento e UI
        if self.vignette_surf.get_size() != surface.get_size():
            vignette = pygame.transform.scale(self.vignette_surf, surface.get_size())
            surface.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        else:
            surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        for ent in visible_entities:
            if ent is not mapa_obj.jogador:
                self.desenhar_barra_flutuante(surface, ent)
        
        for loot in mapa_obj.items_no_chao:
            loot.draw(surface, cam_x, cam_y)

        for txt in mapa_obj.textos:
            txt.draw(surface, cam_x, cam_y)
            
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        if getattr(mapa_obj.context, "debug_enabled", False):
            debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def draw(self, surface, mapa_obj, cor_noite=(0, 0, 0, 0)):
        zoom = getattr(self.camera, "zoom", 1.0)
        is_zoomed = abs(zoom - 1.0) > 0.01

        if not is_zoomed:
            self._render_scene(surface, mapa_obj, cor_noite)
        else:
            view_w = max(32, self.camera.get_view_width())
            view_h = max(32, self.camera.get_view_height())

            if (
                not hasattr(self, "_zoom_surface")
                or self._zoom_surface.get_size() != (view_w, view_h)
            ):
                self._zoom_surface = pygame.Surface((view_w, view_h))

            self._render_scene(self._zoom_surface, mapa_obj, cor_noite)
            pygame.transform.scale(self._zoom_surface, surface.get_size(), surface)

        if getattr(mapa_obj.context, "debug_enabled", False):
            debug.desenhar_hud_f3(surface, self.camera)

    @staticmethod
    def _pond_edge_name(mapa_obj, x, y):
        """Escolhe o autotile do lago a partir das margens vizinhas e cantos diagonais."""
        land = set()
        for dx, dy, side in (
            (0, -1, "north"),
            (0, 1, "south"),
            (-1, 0, "west"),
            (1, 0, "east"),
        ):
            neighbor = mapa_obj.obter_tile(x + dx, y + dy)
            if neighbor and neighbor.tipo not in {"deep_water", "bridge"}:
                land.add(side)

        for first, second, name in (
            ("north", "west", "north_west"),
            ("north", "east", "north_east"),
            ("south", "west", "south_west"),
            ("south", "east", "south_east"),
        ):
            if first in land and second in land:
                return name
        for side in ("north", "south", "west", "east"):
            if side in land:
                return side

        # Cantos internos (côncavos) quando não há terra nos quatro lados cardinais:
        for dx, dy, name in (
            (-1, -1, "inner_north_west"),
            (1, -1, "inner_north_east"),
            (-1, 1, "inner_south_west"),
            (1, 1, "inner_south_east"),
        ):
            neighbor = mapa_obj.obter_tile(x + dx, y + dy)
            if neighbor and neighbor.tipo not in {"deep_water", "bridge"}:
                return name

        return None

    def adicionar_transicoes(self, mapa_obj, tile_type, x, y, sx, sy, queue):
        neighbors = (
            (0, -1, "top"),
            (0, 1, "bottom"),
            (-1, 0, "left"),
            (1, 0, "right"),
        )
        diagonals = (
            (-1, -1, "top_left", (-1, 0), (0, -1)),
            (1, -1, "top_right", (1, 0), (0, -1)),
            (-1, 1, "bottom_left", (-1, 0), (0, 1)),
            (1, 1, "bottom_right", (1, 0), (0, 1)),
        )
        land_types = {"coast", "grass", "terra", "rubble", "mud", "parede"}
        path_types = {"terra", "estrada"}

        def get_prefix(curr, neighbor_type):
            if neighbor_type == "blue_ground" and curr in {"grass", "terra", "rubble", "mud", "coast", "sand", "deep_water"}:
                return "moss_edge"
            elif neighbor_type in path_types and curr in {"grass", "coast", "sand"}:
                return "dirt_edge"
            elif neighbor_type == "grass" and curr in {"coast", "sand", "terra", "mud", "rubble"}:
                return "grass_edge"
            elif neighbor_type in {"rubble", "parede"} and curr in {"terra", "mud", "sand"}:
                return "rubble_edge"
            elif neighbor_type == "coast" and curr == "sand":
                return "coast_edge"
            elif neighbor_type in {"sand", "coast"} and curr == "deep_water":
                return "sand_edge"
            return None

        for dx, dy, side in neighbors:
            neighbor = mapa_obj.obter_tile(x + dx, y + dy)
            if not neighbor:
                continue

            prefix = get_prefix(tile_type, neighbor.tipo)
            image = recursos.SPRITES.get(f"{prefix}_{side}") if prefix else None
            if image:
                queue.append((config.LAYER_CHAO + 0.5, sy, image, sx, sy))

        for dx, dy, corner_name, (c1x, c1y), (c2x, c2y) in diagonals:
            neighbor = mapa_obj.obter_tile(x + dx, y + dy)
            if not neighbor:
                continue
            prefix = get_prefix(tile_type, neighbor.tipo)
            if prefix:
                n1 = mapa_obj.obter_tile(x + c1x, y + c1y)
                n2 = mapa_obj.obter_tile(x + c2x, y + c2y)
                n1_type = n1.tipo if n1 else None
                n2_type = n2.tipo if n2 else None
                if n1_type != neighbor.tipo and n2_type != neighbor.tipo:
                    image = recursos.SPRITES.get(f"{prefix}_{corner_name}")
                    if image:
                        queue.append((config.LAYER_CHAO + 0.5, sy, image, sx, sy))

    def desenhar_barra_flutuante(self, surface, ent):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        screen_x = ent.physics.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.physics.y * config.TAMANHO_TILE - self.camera.camera_y
        largura, altura = 32, 4
        x, y = screen_x, screen_y - 12
        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, largura, altura), 1)
