def convert_daily(value):
    if value == "Calyx_Crimson_Hunt":
        value = "Calyx_Crimson_The_Hunt"
    return value


def convert_20_dungeon(value):
    if value == 'Calyx_Golden_Memories':
        return 'Calyx_Golden_Memories_Jarilo_VI'
    if value == 'Calyx_Golden_Aether':
        return 'Calyx_Golden_Aether_Jarilo_VI'
    if value == 'Calyx_Golden_Treasures':
        return 'Calyx_Golden_Treasures_Jarilo_VI'
    if value == 'Calyx_Golden_Memories':
        return 'Calyx_Golden_Memories_Jarilo_VI'

    if value == 'Calyx_Crimson_Destruction':
        return 'Calyx_Crimson_Destruction_Herta_StorageZone'
    if value == 'Calyx_Crimson_The_Hunt':
        return 'Calyx_Crimson_The_Hunt_Jarilo_OutlyingSnowPlains'
    if value == 'Calyx_Crimson_Erudition':
        return 'Calyx_Crimson_Erudition_Jarilo_RivetTown'
    if value == 'Calyx_Crimson_Harmony':
        return 'Calyx_Crimson_Harmony_Jarilo_RobotSettlement'
    if value == 'Calyx_Crimson_Nihility':
        return 'Calyx_Crimson_Nihility_Jarilo_GreatMine'
    if value == 'Calyx_Crimson_Preservation':
        return 'Calyx_Crimson_Preservation_Herta_SupplyZone'
    if value == 'Calyx_Crimson_Abundance':
        return 'Calyx_Crimson_Abundance_Jarilo_BackwaterPass'

    return value
