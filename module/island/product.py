from module.template.assets import *

def get_product_template(name: str):
    name = name.lower()
    # Ores
    if name == 'coal':
        return TEMPLATE_ISLAND_ORE_T1
    if name == 'copper':
        return TEMPLATE_ISLAND_ORE_T2
    if name == 'aluminum':
        return TEMPLATE_ISLAND_ORE_T3
    if name == 'iron':
        return None
        return TEMPLATE_ISLAND_ORE_T4 # scroll not implemented
    # Woods
    if name == 'raw':
        return TEMPLATE_ISLAND_WOOD_T1
    if name == 'useful':
        return TEMPLATE_ISLAND_WOOD_T2
    if name == 'premium':
        return TEMPLATE_ISLAND_WOOD_T3
    if name == 'elegant':
        return None
        return TEMPLATE_ISLAND_WOOD_T4 # not implemented
    # ---
    return None