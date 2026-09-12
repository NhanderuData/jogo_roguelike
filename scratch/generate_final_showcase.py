import sys
sys.path.insert(0, 'src')
import os
import pygame
from core import config
from graphics import recursos

pygame.init()
screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)

recursos.carregar_tudo()

# -------------------------------------------------------------
# 1. SHOWCASE: LINEUP COMPARING PLAYER, CROPS, AND ALL 13 ANIMALS
# -------------------------------------------------------------
showcase_w, showcase_h = 1360, 420
showcase = pygame.Surface((showcase_w, showcase_h))
# Fill with cozy grass background
grass_tile = recursos.SPRITES.get("terrain_grass")
if isinstance(grass_tile, list): grass_tile = grass_tile[0]
for y in range(0, showcase_h, 32):
    for x in range(0, showcase_w, 32):
        showcase.blit(grass_tile, (x, y))

# Dark banner at top
banner = pygame.Surface((showcase_w, 50))
banner.fill((20, 28, 20))
banner.set_alpha(220)
showcase.blit(banner, (0, 0))

font_title = pygame.font.SysFont("Arial", 22, bold=True)
font_lbl = pygame.font.SysFont("Arial", 13, bold=True)
font_dim = pygame.font.SysFont("Arial", 11)

t_surf = font_title.render("Validação de Escala Proporcional: Jogador vs 13 Animais", True, (255, 235, 170))
showcase.blit(t_surf, (20, 12))

def make_shadow(img, scale_sombra=1.0):
    mask = pygame.mask.from_surface(img)
    sombra = mask.to_surface(setcolor=(0, 0, 0, 85), unsetcolor=(0, 0, 0, 0))
    w, h = sombra.get_size()
    sombra = pygame.transform.scale(sombra, (w, max(1, int(h * 0.45 * scale_sombra))))
    return sombra

ground_y = 290

# Player
player_frame = recursos.SPRITES["player_survivor"]["idle"]["down"][0]
p_w, p_h = player_frame.get_size()
p_bbox = player_frame.get_bounding_rect()
px = 60
p_draw_x = px - p_w // 2
p_draw_y = ground_y - p_h
p_shadow = make_shadow(player_frame, 1.0)
showcase.blit(p_shadow, (p_draw_x, ground_y - p_shadow.get_height() - 2))
showcase.blit(player_frame, (p_draw_x, p_draw_y))

lbl = font_lbl.render("Jogador", True, (255, 255, 100))
dim = font_dim.render(f"{p_bbox.w}x{p_bbox.h}px", True, (220, 220, 220))
showcase.blit(lbl, (px - lbl.get_width()//2, ground_y + 12))
showcase.blit(dim, (px - dim.get_width()//2, ground_y + 28))

# Crops
beet = recursos.SPRITES.get("beterraba_3")
if beet:
    bx = 130
    showcase.blit(beet, (bx - 16, ground_y - 28))
    lbl = font_lbl.render("Horta", True, (150, 255, 150))
    dim = font_dim.render("32x32px", True, (200, 200, 200))
    showcase.blit(lbl, (bx - lbl.get_width()//2, ground_y + 12))
    showcase.blit(dim, (bx - dim.get_width()//2, ground_y + 28))

# 13 Animals
animals_list = [
    ("Touro", "animal_bull", 1.6),
    ("Bezerro", "animal_calf", 1.4),
    ("Cervo", "animal_deer", 1.4),
    ("Javali", "animal_boar", 1.3),
    ("Ovelha", "animal_sheep", 1.2),
    ("Porquinho", "animal_piglet", 1.1),
    ("Raposa", "animal_fox", 1.1),
    ("Cordeiro", "animal_lamb", 1.0),
    ("Peru", "animal_turkey", 1.1),
    ("Lebre", "animal_hare", 0.9),
    ("Tetraz", "animal_black_grouse", 1.0),
    ("Galo", "animal_rooster", 0.9),
    ("Pintinho", "animal_chick", 0.7),
]

cur_x = 210
spacing = 88

for pt_name, sprite_key, s_scale in animals_list:
    frame = recursos.SPRITES[sprite_key]["idle"]["down"][0]
    fw, fh = frame.get_size()
    bb = frame.get_bounding_rect()
    
    draw_x = cur_x - fw // 2
    draw_y = ground_y - fh
    
    shadow = make_shadow(frame, s_scale)
    sw, sh = shadow.get_size()
    
    showcase.blit(shadow, (draw_x, ground_y - sh - 2))
    showcase.blit(frame, (draw_x, draw_y))
    
    lbl = font_lbl.render(pt_name, True, (255, 255, 255))
    dim = font_dim.render(f"{bb.w}x{bb.h}px", True, (200, 230, 255))
    showcase.blit(lbl, (cur_x - lbl.get_width()//2, ground_y + 12))
    showcase.blit(dim, (cur_x - dim.get_width()//2, ground_y + 28))
    
    cur_x += spacing

# Ground line
pygame.draw.line(showcase, (100, 160, 80), (30, ground_y), (showcase_w - 30, ground_y), 2)

showcase_path = "C:/Users/rafae/.gemini/antigravity-ide/brain/bb1cab2e-6a0d-4418-adf7-05992c55c32f/all_animals_showcase.png"
pygame.image.save(showcase, showcase_path)
print("Saved showcase to:", showcase_path)

# -------------------------------------------------------------
# 2. IN-GAME WORLD RENDERING (Actual gameplay scene)
# -------------------------------------------------------------
world_w, world_h = 1280, 720
world = pygame.Surface((world_w, world_h))

dirt_tile = recursos.SPRITES.get("terrain_dirt")
if isinstance(dirt_tile, list): dirt_tile = dirt_tile[0]
water_tile = recursos.SPRITES.get("terrain_water")
if isinstance(water_tile, list): water_tile = water_tile[0]

# Base grass
for y in range(0, world_h, 32):
    for x in range(0, world_w, 32):
        world.blit(grass_tile, (x, y))

# Farm dirt enclosure (left-middle)
for y in range(128, 480, 32):
    for x in range(96, 608, 32):
        world.blit(dirt_tile, (x, y))

# Lake on the right
for y in range(352, 640, 32):
    for x in range(864, 1216, 32):
        world.blit(water_tile, (x, y))

# Lake borders
lake_t = recursos.SPRITES.get("water_edge_top")
lake_b = recursos.SPRITES.get("water_edge_bottom")
lake_l = recursos.SPRITES.get("water_edge_left")
lake_r = recursos.SPRITES.get("water_edge_right")
if lake_t:
    for x in range(864, 1216, 32):
        world.blit(lake_t, (x, 352))
        world.blit(lake_b, (x, 608))
    for y in range(352, 640, 32):
        world.blit(lake_l, (864, y))
        world.blit(lake_r, (1184, y))

# Wooden fences around farm
fence_v = recursos.SPRITES.get("tile_cerca_v", recursos.SPRITES.get("cerca_madeira"))
fence_h = recursos.SPRITES.get("tile_cerca_h", recursos.SPRITES.get("cerca_madeira"))
if fence_v and fence_h:
    for x in range(96, 608, 32):
        if not (320 <= x <= 384): # gate opening
            world.blit(fence_h, (x, 128))
            world.blit(fence_h, (x, 448))
    for y in range(128, 480, 32):
        world.blit(fence_v, (96, y))
        world.blit(fence_v, (576, y))

# Crops inside farm
cabbage = recursos.SPRITES.get("repolho_3")
turnip = recursos.SPRITES.get("nabo_3")
for row_idx, cy in enumerate([192, 256, 320]):
    for col_idx, cx in enumerate(range(160, 300, 48)):
        crop = [beet, cabbage, turnip][(row_idx + col_idx) % 3]
        if crop:
            world.blit(crop, (cx, cy))

# Trees
tree = recursos.SPRITES.get("tree")
tree_red = recursos.SPRITES.get("red_tree", tree)
tree_fir = recursos.SPRITES.get("tree_fir", tree)
if tree:
    world.blit(tree, (640, 80))
    world.blit(tree_red, (730, 40))
    world.blit(tree_fir, (680, 200))
    world.blit(tree, (30, 480))
    world.blit(tree, (1120, 100))
    world.blit(tree_fir, (1180, 240))

# Farm animals inside farm
farm_placements = [
    ("animal_bull", 440, 220, 1.6),
    ("animal_calf", 500, 240, 1.4),
    ("animal_sheep", 370, 350, 1.2),
    ("animal_lamb", 430, 370, 1.0),
    ("animal_piglet", 490, 360, 1.1),
    ("animal_turkey", 340, 240, 1.1),
    ("animal_rooster", 220, 370, 0.9),
    ("animal_chick", 260, 380, 0.7),
]

# Wild animals in forest and near lake
wild_placements = [
    ("animal_deer", 820, 180, 1.4),
    ("animal_boar", 750, 300, 1.3),
    ("animal_fox", 710, 420, 1.1),
    ("animal_hare", 840, 300, 0.9),
    ("animal_black_grouse", 800, 480, 1.0),
]

# Player standing near farm entrance
world_player_x, world_player_y = 352, 490

# Draw entities sorted by Y
render_entities = []
# Player
render_entities.append((world_player_y, "player", player_frame, world_player_x, world_player_y, 1.0))
# Animals
for sp_key, ax, ay, s_scale in farm_placements + wild_placements:
    f = recursos.SPRITES[sp_key]["idle"]["down"][0]
    render_entities.append((ay, sp_key, f, ax, ay, s_scale))

render_entities.sort(key=lambda item: item[0])

for y_pos, ent_type, frame, ex, ey, s_scale in render_entities:
    fw, fh = frame.get_size()
    draw_x = ex + 16 - fw // 2
    draw_y = ey + 32 - fh
    
    shadow = make_shadow(frame, s_scale)
    sw, sh = shadow.get_size()
    world.blit(shadow, (draw_x, (draw_y + fh) - sh - 2))
    world.blit(frame, (draw_x, draw_y))

# Vignette / subtle ambient
vignette = pygame.Surface((world_w, world_h), pygame.SRCALPHA)
pygame.draw.rect(vignette, (0, 0, 0, 20), (0, 0, world_w, world_h))
world.blit(vignette, (0, 0))

# HUD badge
badge = pygame.Surface((340, 42))
badge.fill((15, 20, 15))
badge.set_alpha(200)
world.blit(badge, (16, 16))
hud_txt = font_title.render("Mundo Vivo: 13 Animais Validados", True, (255, 255, 255))
world.blit(hud_txt, (26, 22))

world_path = "C:/Users/rafae/.gemini/antigravity-ide/brain/bb1cab2e-6a0d-4418-adf7-05992c55c32f/ingame_animals_world.png"
pygame.image.save(world, world_path)
print("Saved in-game world to:", world_path)
