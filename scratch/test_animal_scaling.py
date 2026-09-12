import sys
sys.path.insert(0, 'src')
import os
import pygame
from core import config
from graphics import recursos

pygame.init()
screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)

recursos.carregar_tudo()

farm_configs = {
    "animal_bull": ("bull.png", (64, 64), 2.5),
    "animal_calf": ("calf.png", (64, 64), 2.4),
    "animal_chick": ("chick.png", (16, 16), 2.0),
    "animal_lamb": ("lamb.png", (32, 32), 1.8),
    "animal_piglet": ("piglet.png", (32, 32), 2.2),
    "animal_rooster": ("rooster.png", (32, 32), 1.5),
    "animal_sheep": ("sheep.png", (32, 32), 2.0),
    "animal_turkey": ("turkey.png", (32, 32), 1.6),
}

hunt_configs = {
    "animal_boar": ("boar", "boar_idle.png", "boar_walk.png", 2.4),
    "animal_deer": ("deer", "deer_idle.png", "deer_walk.png", 2.6),
    "animal_fox": ("fox", "fox_idle.png", "fox_walk.png", 2.0),
    "animal_hare": ("hare", "hare_idle.png", "hare_walk.png", 1.6),
    "animal_black_grouse": ("black_grouse", "black_grouse_idle.png", "black_grouse_walk.png", 1.6),
}

def load_scaled_farm():
    animais = {}
    for key, (filename, (fw, fh), scale) in farm_configs.items():
        sheet = pygame.image.load(f"assets/sprites/animals/farm/{filename}").convert_alpha()
        # compute max_bottom across rows 0-7, cols 0-5
        cols = min(6, sheet.get_width() // fw)
        rows = min(8, sheet.get_height() // fh)
        max_b = 0
        for r in range(rows):
            for c in range(cols):
                sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, fh))
                bb = sub.get_bounding_rect()
                if bb.w > 0 and bb.h > 0:
                    max_b = max(max_b, bb.bottom)
        crop_h = min(fh, max_b + 1)
        target_w = int(fw * scale)
        target_h = int(crop_h * scale)

        def get_row(row, count):
            frames = []
            for col in range(count):
                sub = sheet.subsurface(pygame.Rect(col * fw, row * fh, fw, crop_h))
                frames.append(pygame.transform.scale(sub, (target_w, target_h)))
            return frames

        animais[key] = {
            "idle": {
                "down": get_row(4, 4),
                "up": get_row(5, 4),
                "left": get_row(6, 4),
                "right": get_row(7, 4),
            },
            "move": {
                "down": get_row(0, 6),
                "up": get_row(1, 6),
                "left": get_row(2, 6),
                "right": get_row(3, 6),
            },
        }
    return animais

def load_scaled_hunt():
    animais = {}
    fw, fh = 32, 32
    for key, (folder, idle_file, walk_file, scale) in hunt_configs.items():
        idle_sheet = pygame.image.load(f"assets/sprites/animals/hunt/{folder}/{idle_file}").convert_alpha()
        walk_sheet = pygame.image.load(f"assets/sprites/animals/hunt/{folder}/{walk_file}").convert_alpha()
        
        # compute max_bottom
        max_b = 0
        for sheet in (idle_sheet, walk_sheet):
            c_cnt = sheet.get_width() // fw
            r_cnt = sheet.get_height() // fh
            for r in range(r_cnt):
                for c in range(c_cnt):
                    sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, fh))
                    bb = sub.get_bounding_rect()
                    if bb.w > 0 and bb.h > 0:
                        max_b = max(max_b, bb.bottom)
        crop_h = min(fh, max_b + 1)
        target_w = int(fw * scale)
        target_h = int(crop_h * scale)

        def load_action(sheet):
            cols = sheet.get_width() // fw
            dirs = {}
            for r, dir_name in enumerate(["down", "up", "left", "right"]):
                frames = []
                for c in range(cols):
                    sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, crop_h))
                    frames.append(pygame.transform.scale(sub, (target_w, target_h)))
                dirs[dir_name] = frames
            return dirs

        animais[key] = {
            "idle": load_action(idle_sheet),
            "move": load_action(walk_sheet),
        }
    return animais

new_farm = load_scaled_farm()
new_hunt = load_scaled_hunt()
all_animals = {**new_farm, **new_hunt}

# Create a scene canvas (1280 x 720)
scene = pygame.Surface((1280, 720))
# Fill with grass tiles
grass = recursos.SPRITES.get("terrain_grass")
dirt = recursos.SPRITES.get("terrain_dirt")
if isinstance(grass, list): grass = grass[0]
if isinstance(dirt, list): dirt = dirt[0]

for y in range(0, 720, 32):
    for x in range(0, 1280, 32):
        scene.blit(grass, (x, y))

# Draw dirt patch for farm area
for y in range(80, 480, 32):
    for x in range(160, 640, 32):
        scene.blit(dirt, (x, y))

# Draw fences and crops
fence = recursos.SPRITES.get("tile_cerca_v", recursos.SPRITES.get("cerca_madeira"))
if fence:
    for y in range(80, 480, 32):
        scene.blit(fence, (160, y))
        scene.blit(fence, (640, y))

# Crops
beet = recursos.SPRITES.get("beterraba_3")
cabbage = recursos.SPRITES.get("repolho_3")
turnip = recursos.SPRITES.get("nabo_3")
crops = [beet, cabbage, turnip]
crop_idx = 0
for cy in [160, 240, 320]:
    for cx in range(220, 580, 64):
        c_img = crops[crop_idx % len(crops)]
        if c_img:
            scene.blit(c_img, (cx, cy))
        crop_idx += 1

# Trees
tree = recursos.SPRITES.get("tree")
if tree:
    scene.blit(tree, (20, 100))
    scene.blit(tree, (1000, 80))
    scene.blit(tree, (1080, 260))

# Shadow helper
def make_shadow(img, scale_sombra=1.0):
    mask = pygame.mask.from_surface(img)
    sombra = mask.to_surface(setcolor=(0, 0, 0, 75), unsetcolor=(0, 0, 0, 0))
    w, h = sombra.get_size()
    sombra = pygame.transform.scale(sombra, (w, max(1, int(h * 0.45 * scale_sombra))))
    return sombra

# Draw player
player_frame = recursos.SPRITES["player_survivor"]["idle"]["down"][0]
px, py = 400, 400
p_shadow = make_shadow(player_frame, 1.0)
scene.blit(p_shadow, (px + (32 - p_shadow.get_width())//2, py + 32 - p_shadow.get_height() - 2))
scene.blit(player_frame, (px + (32 - player_frame.get_width())//2, py + 32 - player_frame.get_height()))

# Animal shadow scale presets
shadow_scales = {
    "animal_bull": 1.6,
    "animal_calf": 1.4,
    "animal_chick": 0.7,
    "animal_lamb": 1.0,
    "animal_piglet": 1.1,
    "animal_rooster": 0.9,
    "animal_sheep": 1.2,
    "animal_turkey": 1.0,
    "animal_boar": 1.3,
    "animal_deer": 1.4,
    "animal_fox": 1.1,
    "animal_hare": 0.9,
    "animal_black_grouse": 1.0,
}

# Positions for animals
positions = [
    ("animal_bull", 220, 420),
    ("animal_calf", 290, 430),
    ("animal_sheep", 350, 440),
    ("animal_lamb", 470, 430),
    ("animal_piglet", 520, 440),
    ("animal_turkey", 580, 420),
    ("animal_rooster", 430, 450),
    ("animal_chick", 400, 470),
    ("animal_boar", 740, 320),
    ("animal_deer", 820, 240),
    ("animal_fox", 740, 440),
    ("animal_hare", 820, 420),
    ("animal_black_grouse", 880, 340),
]

font = pygame.font.SysFont("Arial", 14, bold=True)

for name, ax, ay in positions:
    frame = all_animals[name]["idle"]["down"][0]
    s_scale = shadow_scales.get(name, 1.0)
    shadow = make_shadow(frame, s_scale)
    
    img_w, img_h = frame.get_size()
    draw_x = ax + 16 - img_w // 2
    draw_y = ay + 32 - img_h
    
    s_w, s_h = shadow.get_size()
    s_x = draw_x
    s_y = (draw_y + img_h) - s_h - 2
    
    scene.blit(shadow, (s_x, s_y))
    scene.blit(frame, (draw_x, draw_y))
    
    # Label
    lbl = font.render(name.replace("animal_", ""), True, (255, 255, 255))
    lbl_bg = pygame.Surface((lbl.get_width() + 4, lbl.get_height() + 2))
    lbl_bg.fill((0, 0, 0))
    lbl_bg.set_alpha(160)
    scene.blit(lbl_bg, (draw_x + (img_w - lbl.get_width())//2 - 2, draw_y - 18))
    scene.blit(lbl, (draw_x + (img_w - lbl.get_width())//2, draw_y - 17))

# Player label
p_lbl = font.render("PLAYER", True, (255, 255, 0))
scene.blit(p_lbl, (px - 10, py - 40))

artifact_path = "C:/Users/rafae/.gemini/antigravity-ide/brain/bb1cab2e-6a0d-4418-adf7-05992c55c32f/ingame_animals_scaled.png"
pygame.image.save(scene, artifact_path)
print("Saved preview to:", artifact_path)
