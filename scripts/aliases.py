# -*- coding: utf-8 -*-
# Curated old(1.8.9) -> new(26.1.2) basename rename tables.
# Built by manually cross-referencing the real file lists extracted from both
# uploaded packs (not guessed from memory alone), plus verified web research
# for historically tricky cases (e.g. dye subtype reuse).
#
# All names are WITHOUT extension. Colors lists follow vanilla's 16-dye set.

COLORS = ["black","blue","brown","cyan","gray","green","light_blue","lime",
          "magenta","orange","pink","purple","red","silver","white","yellow"]
# old "silver" == new "light_gray" (renamed well before 1.13, but the old
# 1.8.9 file names still use the legacy "silver" token)
NEW_COLOR = {c: ("light_gray" if c == "silver" else c) for c in COLORS}

BLOCK_ALIASES = {}
ITEM_ALIASES = {}
ENTITY_ALIASES = {}   # deprecated - see ENTITY_ALIASES_LIST below

# ---------------------------------------------------------------- BLOCKS ---
BLOCK_ALIASES.update({
    # stone family
    "stone_andesite": "andesite",
    "stone_andesite_smooth": "polished_andesite",
    "stone_diorite": "diorite",
    "stone_diorite_smooth": "polished_diorite",
    "stone_granite": "granite",
    "stone_granite_smooth": "polished_granite",
    "stonebrick": "stone_bricks",
    "stonebrick_mossy": "mossy_stone_bricks",
    "stonebrick_cracked": "cracked_stone_bricks",
    "stonebrick_carved": "chiseled_stone_bricks",
    "cobblestone_mossy": "mossy_cobblestone",
    "stone_slab_top": "smooth_stone",
    "stone_slab_side": "smooth_stone_slab_side",
    "brick": "bricks",
    "nether_brick": "nether_bricks",

    # sandstone
    "sandstone_carved": "chiseled_sandstone",
    "sandstone_smooth": "cut_sandstone",
    "sandstone_normal": "sandstone",
    "red_sandstone_carved": "chiseled_red_sandstone",
    "red_sandstone_smooth": "cut_red_sandstone",
    "red_sandstone_normal": "red_sandstone",

    # quartz
    "quartz_block_chiseled": "chiseled_quartz_block",
    "quartz_block_chiseled_top": "chiseled_quartz_block_top",
    "quartz_block_lines": "quartz_pillar",
    "quartz_block_lines_top": "quartz_pillar_top",

    # wood: material_type -> type_material, "big_oak"/"roofed_oak" -> "dark_oak"
    **{f"log_{w}": f"{w}_log" for w in ["oak","spruce","birch","jungle","acacia"]},
    **{f"log_{w}_top": f"{w}_log_top" for w in ["oak","spruce","birch","jungle","acacia"]},
    "log_big_oak": "dark_oak_log",
    "log_big_oak_top": "dark_oak_log_top",
    **{f"leaves_{w}": f"{w}_leaves" for w in ["oak","spruce","birch","jungle","acacia"]},
    "leaves_big_oak": "dark_oak_leaves",
    **{f"planks_{w}": f"{w}_planks" for w in ["oak","spruce","birch","jungle","acacia"]},
    "planks_big_oak": "dark_oak_planks",
    **{f"sapling_{w}": f"{w}_sapling" for w in ["oak","spruce","birch","jungle","acacia"]},
    "sapling_roofed_oak": "dark_oak_sapling",

    # doors: material_lower/upper -> material_bottom/top ; "wood"->"oak"
    "door_wood_lower": "oak_door_bottom", "door_wood_upper": "oak_door_top",
    "door_acacia_lower": "acacia_door_bottom", "door_acacia_upper": "acacia_door_top",
    "door_birch_lower": "birch_door_bottom", "door_birch_upper": "birch_door_top",
    "door_jungle_lower": "jungle_door_bottom", "door_jungle_upper": "jungle_door_top",
    "door_spruce_lower": "spruce_door_bottom", "door_spruce_upper": "spruce_door_top",
    "door_dark_oak_lower": "dark_oak_door_bottom", "door_dark_oak_upper": "dark_oak_door_top",
    "door_iron_lower": "iron_door_bottom", "door_iron_upper": "iron_door_top",

    # the only 1.8.9 trapdoor (generic "wood") maps to the new oak-specific one;
    # other new wood-species trapdoors have no 1.8.9 source (see report)
    "trapdoor": "oak_trapdoor",

    # wool / dyed colors
    **{f"wool_colored_{c}": f"{NEW_COLOR[c]}_wool" for c in COLORS},
    # stained glass
    **{f"glass_{c}": f"{NEW_COLOR[c]}_stained_glass" for c in COLORS},
    **{f"glass_pane_top_{c}": f"{NEW_COLOR[c]}_stained_glass_pane_top" for c in COLORS},
    # terracotta (hardened clay)
    "hardened_clay": "terracotta",
    **{f"hardened_clay_stained_{c}": f"{NEW_COLOR[c]}_terracotta" for c in COLORS},

    # grass / dirt
    "grass_top": "grass_block_top",
    "grass_side": "grass_block_side",
    "grass_side_overlay": "grass_block_side_overlay",
    "grass_side_snowed": "grass_block_snow",
    "dirt_podzol_top": "podzol_top",
    "dirt_podzol_side": "podzol_side",
    "farmland_dry": "farmland",
    "farmland_wet": "farmland_moist",

    # flowers (single-block)
    "flower_rose": "poppy",                 # "Rose" was renamed "Poppy" in 1.9
    "flower_houstonia": "azure_bluet",      # old codename "Houstonia"
    "flower_tulip_orange": "orange_tulip",
    "flower_tulip_pink": "pink_tulip",
    "flower_tulip_red": "red_tulip",
    "flower_tulip_white": "white_tulip",
    "flower_allium": "allium",
    "flower_blue_orchid": "blue_orchid",
    "flower_dandelion": "dandelion",
    "flower_oxeye_daisy": "oxeye_daisy",
    # flower_paeonia: NOT mapped - visually distinct unused/vestigial 1.8.9
    # texture, not actually the double-plant Peony (see report)

    # double (2-tall) plants
    "double_plant_fern_bottom": "large_fern_bottom",
    "double_plant_fern_top": "large_fern_top",
    "double_plant_grass_bottom": "tall_grass_bottom",
    "double_plant_grass_top": "tall_grass_top",
    "double_plant_paeonia_bottom": "peony_bottom",
    "double_plant_paeonia_top": "peony_top",
    "double_plant_rose_bottom": "rose_bush_bottom",
    "double_plant_rose_top": "rose_bush_top",
    "double_plant_syringa_bottom": "lilac_bottom",
    "double_plant_syringa_top": "lilac_top",
    "double_plant_sunflower_back": "sunflower_back",
    "double_plant_sunflower_bottom": "sunflower_bottom",
    "double_plant_sunflower_front": "sunflower_front",
    "double_plant_sunflower_top": "sunflower_top",
    "tallgrass": "short_grass",
    "waterlily": "lily_pad",
    "reeds": "sugar_cane",

    # redstone components
    "redstone_lamp_off": "redstone_lamp",
    "redstone_torch_on": "redstone_torch",
    "torch_on": "torch",
    "comparator_off": "comparator",
    "repeater_off": "repeater",
    "redstone_dust_line": "redstone_dust_line0",   # best-effort; see report
    # NOTE: redstone_dust_cross / cross_overlay / line_overlay intentionally
    # left unmapped - the wire rendering system was redesigned (tint-based
    # overlays + a small dot instead of a big cross sprite); no faithful 1:1.

    # pumpkin / melon stems + faces
    "pumpkin_face_off": "carved_pumpkin",
    "pumpkin_face_on": "jack_o_lantern",
    "pumpkin_stem_connected": "attached_pumpkin_stem",
    "pumpkin_stem_disconnected": "pumpkin_stem",
    "melon_stem_connected": "attached_melon_stem",
    "melon_stem_disconnected": "melon_stem",

    # rails
    "rail_activator": "activator_rail",
    "rail_activator_powered": "activator_rail_on",
    "rail_detector": "detector_rail",
    "rail_detector_powered": "detector_rail_on",
    "rail_golden": "powered_rail",
    "rail_golden_powered": "powered_rail_on",
    "rail_normal": "rail",
    "rail_normal_turned": "rail_corner",

    "piston_top_normal": "piston_top",

    "dispenser_front_horizontal": "dispenser_front",
    "dropper_front_horizontal": "dropper_front",
    "furnace_front_off": "furnace_front",

    "endframe_eye": "end_portal_frame_eye",
    "endframe_side": "end_portal_frame_side",
    "endframe_top": "end_portal_frame_top",

    "anvil_base": "anvil",
    "anvil_top_damaged_0": "anvil_top",
    "anvil_top_damaged_1": "chipped_anvil_top",
    "anvil_top_damaged_2": "damaged_anvil_top",

    "carrots_stage_0": "carrots_stage0", "carrots_stage_1": "carrots_stage1",
    "carrots_stage_2": "carrots_stage2", "carrots_stage_3": "carrots_stage3",
    "cocoa_stage_0": "cocoa_stage0", "cocoa_stage_1": "cocoa_stage1", "cocoa_stage_2": "cocoa_stage2",
    "nether_wart_stage_0": "nether_wart_stage0", "nether_wart_stage_1": "nether_wart_stage1",
    "nether_wart_stage_2": "nether_wart_stage2",
    "potatoes_stage_0": "potatoes_stage0", "potatoes_stage_1": "potatoes_stage1",
    "potatoes_stage_2": "potatoes_stage2", "potatoes_stage_3": "potatoes_stage3",
    **{f"wheat_stage_{i}": f"wheat_stage{i}" for i in range(8)},

    "ice_packed": "packed_ice",
    "itemframe_background": "item_frame",
    "mob_spawner": "spawner",
    "mushroom_block_skin_brown": "brown_mushroom_block",
    "mushroom_block_skin_red": "red_mushroom_block",
    "mushroom_block_skin_stem": "mushroom_stem",
    "mushroom_brown": "brown_mushroom",
    "mushroom_red": "red_mushroom",
    "noteblock": "note_block",
    "prismarine_rough": "prismarine",
    "prismarine_dark": "dark_prismarine",
    "slime": "slime_block",
    "sponge_wet": "wet_sponge",
    "trip_wire": "tripwire",
    "trip_wire_source": "tripwire_hook",
    "web": "cobweb",
    "command_block": "command_block_front",
})

# ----------------------------------------------------------------- ITEMS ---
ITEM_ALIASES.update({
    "apple_golden": "golden_apple",
    "beef_cooked": "cooked_beef", "beef_raw": "beef",
    "boat": "oak_boat",
    "book_enchanted": "enchanted_book", "book_normal": "book",
    "book_writable": "writable_book", "book_written": "written_book",
    "bow_standby": "bow",
    "bucket_empty": "bucket", "bucket_lava": "lava_bucket",
    "bucket_milk": "milk_bucket", "bucket_water": "water_bucket",
    "carrot_golden": "golden_carrot",
    "chicken_cooked": "cooked_chicken", "chicken_raw": "chicken",
    "door_acacia": "acacia_door", "door_birch": "birch_door",
    "door_dark_oak": "dark_oak_door", "door_iron": "iron_door",
    "door_jungle": "jungle_door", "door_spruce": "spruce_door",
    "door_wood": "oak_door",

    # dye subtype history: black/blue/brown/white were reused *other* items
    # pre-1.14, not standalone dyes (verified: Ink Sac / Lapis Lazuli /
    # Cocoa Beans / Bone Meal). The remaining 12 map straight across.
    "dye_powder_black": "ink_sac",
    "dye_powder_blue": "lapis_lazuli",
    "dye_powder_brown": "cocoa_beans",
    "dye_powder_white": "bone_meal",
    **{f"dye_powder_{c}": f"{NEW_COLOR[c]}_dye"
       for c in COLORS if c not in ("black","blue","brown","white")},

    "fireball": "fire_charge",
    "fireworks": "firework_rocket",
    "fireworks_charge": "firework_star",
    "fireworks_charge_overlay": "firework_star_overlay",
    "fish_clownfish_raw": "tropical_fish",
    "fish_cod_cooked": "cooked_cod", "fish_cod_raw": "cod",
    "fish_pufferfish_raw": "pufferfish",
    "fish_salmon_cooked": "cooked_salmon", "fish_salmon_raw": "salmon",
    "fishing_rod_uncast": "fishing_rod",
    "gold_axe": "golden_axe", "gold_boots": "golden_boots",
    "gold_chestplate": "golden_chestplate", "gold_helmet": "golden_helmet",
    "gold_hoe": "golden_hoe", "gold_horse_armor": "golden_horse_armor",
    "gold_leggings": "golden_leggings", "gold_pickaxe": "golden_pickaxe",
    "gold_shovel": "golden_shovel", "gold_sword": "golden_sword",
    "map_empty": "map", "map_filled": "filled_map",
    "melon": "melon_slice", "melon_speckled": "glistering_melon_slice",
    "minecart_chest": "chest_minecart",
    "minecart_command_block": "command_block_minecart",
    "minecart_furnace": "furnace_minecart",
    "minecart_hopper": "hopper_minecart",
    "minecart_normal": "minecart", "minecart_tnt": "tnt_minecart",
    "mutton_cooked": "cooked_mutton", "mutton_raw": "mutton",
    "netherbrick": "nether_brick",
    "porkchop_cooked": "cooked_porkchop", "porkchop_raw": "porkchop",
    "potato_baked": "baked_potato", "potato_poisonous": "poisonous_potato",
    "potion_bottle_drinkable": "potion", "potion_bottle_empty": "glass_bottle",
    "potion_bottle_splash": "splash_potion",
    "rabbit_cooked": "cooked_rabbit", "rabbit_raw": "rabbit",
    **{f"record_{n}": f"music_disc_{n}" for n in
       ["11","13","blocks","cat","chirp","far","mall","mellohi","stal","strad","wait","ward"]},
    "redstone_dust": "redstone",
    "reeds": "sugar_cane",
    "seeds_melon": "melon_seeds", "seeds_pumpkin": "pumpkin_seeds",
    "seeds_wheat": "wheat_seeds",
    "sign": "oak_sign",
    "slimeball": "slime_ball",
    "spider_eye_fermented": "fermented_spider_eye",
    "wood_axe": "wooden_axe", "wood_hoe": "wooden_hoe",
    "wood_pickaxe": "wooden_pickaxe", "wood_shovel": "wooden_shovel",
    "wood_sword": "wooden_sword",
    "wooden_armorstand": "armor_stand",
})

# Items with NO modern equivalent file at all (system redesigned or texture
# was unused even in 1.8.9) - listed explicitly so the report can explain why,
# instead of just calling them a fuzzy-match failure.
ITEM_NO_EQUIVALENT = {
    "banner_base": "banners are now rendered from the entity/banner texture + pattern layers, not a flat item icon",
    "banner_overlay": "see banner_base",
    "bed": "beds are per-color now and item icon is generated from the entity model, no flat generic 'bed' item icon exists",
    "empty_armor_slot_boots": "moved into gui/sprites/container as GUI slot icons, not an item texture",
    "empty_armor_slot_chestplate": "see empty_armor_slot_boots",
    "empty_armor_slot_helmet": "see empty_armor_slot_boots",
    "empty_armor_slot_leggings": "see empty_armor_slot_boots",
    "quiver": "unused/scrapped texture in 1.8.9 itself - never a functional item",
    "ruby": "unused/scrapped texture in 1.8.9 itself - early placeholder from before Emerald existed",
    "spawn_egg": "spawn eggs are no longer a tinted base+overlay pair; every mob now has a unique pre-painted egg texture",
    "spawn_egg_overlay": "see spawn_egg",
}

ENTITY_ALIASES_LIST = [
    ("alex", "player/slim/alex"),
    ("steve", "player/wide/steve"),
    ("snowman", "snow_golem/snow_golem"),
    ("zombie_pigman", "piglin/zombified_piglin"),
    ("sign", "signs/oak"),
    ("sheep/sheep_fur", "sheep/sheep_wool"),
    ("villager/farmer", "villager/profession/farmer"),
    ("villager/librarian", "villager/profession/librarian"),
    ("villager/priest", "villager/profession/cleric"),
    ("villager/smith", "villager/profession/toolsmith"),
    ("villager/butcher", "villager/profession/butcher"),
    *[(f"rabbit/{n}", f"rabbit/rabbit_{n}") for n in
      ["black", "brown", "caerbannog", "gold", "salt", "toast", "white", "white_splotched"]],
    ("endercrystal/endercrystal", "end_crystal/end_crystal"),
    ("endercrystal/endercrystal_beam", "end_crystal/end_crystal_beam"),
    ("boat", "boat/oak"),
    ("cat/black", "cat/cat_black"),       # verified visually: same white-paw/chest pattern
    ("cat/red", "cat/cat_red"),
    ("cat/siamese", "cat/cat_siamese"),
    # 1.8.9 had one skin per animal; 26.1.2 splits some into biome/coat variants
    # that are cosmetic-only (not a new functional mob) - the base 1.8.9 look
    # is applied to every such variant. Pig/Cow/Mooshroom are EXCLUDED here on
    # purpose: their canvas grew 64x32 -> 64x64 (non-uniform aspect change) so
    # there's no safe pixel mapping without a real UV re-layout - see report.
    ("chicken", "chicken/chicken_temperate"),
    ("chicken", "chicken/chicken_cold"),
    ("chicken", "chicken/chicken_warm"),
    *[("villager/villager", f"villager/type/{b}") for b in
      ["desert", "jungle", "plains", "savanna", "snow", "swamp", "taiga"]],
    *[(f"wolf/{base}", f"wolf/wolf_{coat}{suffix}")
      for coat in ["ashen", "black", "chestnut", "rusty", "snowy", "spotted", "striped", "woods"]
      for base, suffix in [("wolf", ""), ("wolf_angry", "_angry"), ("wolf_tame", "_tame")]],
    *[("cat/black", f"cat/cat_{b}") for b in
      ["all_black", "british_shorthair", "calico", "jellie", "persian", "ragdoll", "tabby", "white"]],
    # shield patterns are the exact same pattern assets as banner patterns
    *[(f"banner/{p}", f"shield/{p}") for p in [
        "base","border","bricks","circle","creeper","cross","curly_border","diagonal_left",
        "diagonal_right","diagonal_up_left","diagonal_up_right","flower","gradient","gradient_up",
        "half_horizontal","half_horizontal_bottom","half_vertical","half_vertical_right","mojang",
        "rhombus","skull","small_stripes","square_bottom_left","square_bottom_right",
        "square_top_left","square_top_right","straight_cross","stripe_bottom","stripe_center",
        "stripe_downleft","stripe_downright","stripe_left","stripe_middle","stripe_right",
        "stripe_top","triangle_bottom","triangle_top","triangles_bottom","triangles_top"]],
    ("banner/creeper", "banner/creeper"),  # keep explicit (was being shadowed by mob creeper.png)
]
# Old source files "claimed" by an explicit alias above must NOT also be
# eligible for the generic basename-anywhere fallback below - that greedy
# fallback is what let entity/rabbit/white.png leak into entity/bed/white.png,
# entity/rabbit/gold.png leak into entity/equipment/*/gold.png, etc, purely
# because they happen to share a generic basename like "white" or "gold".
ENTITY_ALIAS_CLAIMED_SOURCES = set(old_key for old_key, _ in ENTITY_ALIASES_LIST)

# mobs/entities to explicitly exclude from the "_baby reuses adult" rule even
# though a same-dimension source exists - confirmed by direct testing that
# the baby model does NOT actually share the adult's UV layout here.
BABY_RULE_EXCLUDE = {"sheep/sheep_baby", "sheep/sheep_wool_baby"}

BLOCK_NO_EQUIVALENT = {
    "flower_paeonia": "visually distinct from the Peony double-plant texture; appears to be an unused/vestigial 1.8.9 texture",
    "redstone_dust_cross": "redstone wire rendering was redesigned around a small tinted dot instead of a big cross sprite",
    "redstone_dust_cross_overlay": "see redstone_dust_cross",
    "redstone_dust_line_overlay": "the overlay/tint system for wire color was redesigned",
}
