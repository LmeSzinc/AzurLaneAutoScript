SHORTEST_FILTER = """
0:20 > 0:30
> 1 > 1:10 > 1:20 > 1:30 > 1:40 > 1:45
> 2 > 2:15 > 2:30 > 2:40
> 3 > 3:20
> 4 > 5 > 5:20
> 6 > 7 > 8 > 9 > 10 > 12
"""

DICT_FILTER_PRESET = {
    'chip': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > ExtraDrill-5:20 > ExtraDrill-2 > ExtraDrill-3:20 
    > UrgentCube-2:15 > UrgentCube-4
    > ExtraDrill-1 > UrgentCube-6 > ExtraCube-1:30 
    > ExtraDrill-2:40 > ExtraDrill-0:20  
    > Major > DailyChip > DailyResource
    > ExtraPart-0:30 > ExtraOil-1 > UrgentBox-6 
    > ExtraCube-3 > ExtraPart-1 > UrgentBox-3
    > ExtraCube-4 > ExtraPart-1:30 > ExtraOil-4
    > UrgentBox-1 > ExtraCube-5
    > ExtraCube-8 > ExtraOil-8
    > UrgentDrill-4 > UrgentDrill-2:40 > UrgentDrill-2 
    > UrgentDrill-1 > UrgentDrill-1:30 > UrgentDrill-1:10
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'chip_night': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 
    > Major > DailyChip > DailyResource
    > NightDrill-8 > NightDrill-7 > NightDrill-6
    > ExtraDrill-5:20 > UrgentCube-6 > UrgentCube-4
    > ExtraDrill-3:20 > UrgentCube-3 > UrgentBox-6
    > UrgentCube-1:30 > UrgentCube-1:45 > NightCube-8 > ExtraCube-8 > UrgentCube-2:15 
    > NightOil-8 > ExtraOil-8 > ExtraDrill-2 > ExtraDrill-2:40 
    > ExtraCube-0:30 > UrgentBox-3 > ExtraCube-4 > NightCube-6 
    > ExtraCube-1:30 > ExtraCube-5 > NightCube-7 > ExtraCube-3
    > ExtraOil-4 > UrgentDrill-4 > ExtraDrill-1 
    > UrgentDrill-2:40 > UrgentDrill-2
    > UrgentBox-1 > UrgentDrill-1:30 > ExtraDrill-0:20
    > UrgentDrill-1:10 > UrgentDrill-1
    > ExtraOil-1
    > shortest
    """,
    'chip_24h': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > ExtraDrill-5:20 > ExtraDrill-2 > ExtraDrill-3:20 
    > UrgentCube-2:15 > UrgentCube-4
    > ExtraDrill-1 > UrgentCube-6 > ExtraCube-1:30 
    > ExtraDrill-2:40 > ExtraDrill-0:20
    > Major > DailyChip > DailyResource
    > NightDrill-8 > NightDrill-7 > NightDrill-6
    > ExtraPart-0:30 > ExtraOil-1 > UrgentBox-6 
    > ExtraCube-3 > ExtraPart-1 > UrgentBox-3
    > ExtraCube-4 > ExtraPart-1:30 > ExtraOil-4
    > UrgentBox-1 > ExtraCube-5
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'cube': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > UrgentCube-2:15 > UrgentCube-4 > UrgentCube-6 
    > ExtraCube-1:30 > ExtraCube-3 > ExtraCube-4 
    > ExtraCube-8 > UrgentBox-6 > UrgentBox-3 > ExtraCube-5 > UrgentBox-1
    > Major > DailyChip > DailyResource
    > ExtraOil-8 > UrgentDrill-4 > ExtraOil-4 > ExtraOil-1 
    > ExtraDrill-0:20 > UrgentDrill-2:40 > ExtraPart-0:30 
    > UrgentDrill-2 > UrgentDrill-1 > UrgentDrill-1:30
    > ExtraPart-1 > ExtraDrill-1 > UrgentDrill-1:10
    > ExtraPart-1:30 > ExtraDrill-2 
    > ExtraDrill-2:40 > ExtraDrill-3:20 > ExtraDrill-5:20 
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'cube_night': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2  
    > Major > DailyChip > DailyResource
    > UrgentCube-6 > UrgentCube-4 > UrgentCube-3 
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-2:15 
    > NightCube-8 > ExtraCube-8 > UrgentBox-6
    > ExtraCube-0:30 > NightCube-6 > ExtraCube-4 
    > NightOil-8 > ExtraOil-8
    > ExtraCube-1:30 > NightCube-7 > ExtraCube-5 > ExtraCube-3
    > UrgentBox-3 > NightDrill-8 > UrgentDrill-4
    > ExtraOil-4 > NightDrill-7
    > UrgentDrill-2:40 > NightDrill-6 > UrgentDrill-2
    > UrgentBox-1 > UrgentDrill-1:30 > ExtraDrill-5:20 
    > UrgentDrill-1:10 > UrgentDrill-1 > ExtraOil-1
    > ExtraDrill-3:20 > ExtraDrill-2:40 > ExtraDrill-2      
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'cube_24h': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > UrgentCube-2:15 > UrgentCube-4 > UrgentCube-6 
    > ExtraCube-1:30 > ExtraCube-3 > ExtraCube-4 
    > ExtraCube-8 > UrgentBox-6 > UrgentBox-3 > ExtraCube-5 > UrgentBox-1
    > Major > DailyChip > DailyResource
    > ExtraOil-1 > ExtraOil-4 > ExtraOil-8 
    > ExtraPart-0:30 > ExtraPart-1 > ExtraDrill-1
    > ExtraPart-1:30 > ExtraDrill-2 
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'oil': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > UrgentCube-2:15 > UrgentCube-4 
    > UrgentBox-6 > ExtraCube-1:30 > UrgentCube-6 
    > UrgentBox-3 > UrgentBox-1
    > UrgentDrill-4 > ExtraOil-8 > UrgentDrill-2:40 > ExtraOil-4
    > Major > DailyChip > DailyResource
    > ExtraCube-3 > UrgentDrill-2 > UrgentDrill-1
    > UrgentDrill-1:30 > UrgentDrill-1:10 
    > ExtraCube-4 > ExtraOil-1 > ExtraCube-8 > ExtraDrill-0:20
    > ExtraCube-5 > ExtraPart-0:30 > ExtraPart-1
    > ExtraDrill-1 > ExtraPart-1:30 > ExtraDrill-2 
    > ExtraDrill-2:40 > ExtraDrill-3:20 > ExtraDrill-5:20 
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """,
    'oil_night': """
    DailyEvent > Gem-8 > Gem-4 > Gem-2 
    > Major > DailyChip > DailyResource
    > UrgentBox-6 > UrgentCube-6
    > NightOil-8 > ExtraOil-8 > UrgentCube-3
    > UrgentCube-4 > UrgentCube-1:30 > UrgentCube-1:45
    > NightCube-8 > ExtraCube-8 > UrgentCube-2:15 
    > UrgentBox-3 > NightDrill-8 > UrgentDrill-4 > ExtraOil-4
    > ExtraCube-0:30 > NightDrill-7 > NightCube-6 > ExtraCube-4
    > ExtraCube-1:30 > NightCube-7 > ExtraCube-5 > ExtraCube-3
    > UrgentDrill-2:40 > NightDrill-6 > UrgentDrill-2 
    > UrgentBox-1 > UrgentDrill-1:30 > ExtraDrill-5:20
    > UrgentDrill-1:10 > UrgentDrill-1
    > ExtraOil-1 > ExtraDrill-3:20 > ExtraDrill-2:40
    > ExtraPart-1:30 > ExtraDrill-2       
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > shortest
    """
}
