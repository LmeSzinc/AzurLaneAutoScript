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
    DailyEvent
    > Gem-8 > Gem-4 > Gem-2 > ExtraCube-0:30 
    > NightDrill-6 > ExtraDrill-2 > NightDrill-7 > NightDrill-8 
    > ExtraDrill-3:20 > ExtraDrill-5:20 > ExtraDrill-0:20 > ExtraDrill-1 > ExtraDrill-2:40 
    > UrgentCube-1:30 > UrgentCube-1:45 > UrgentCube-3 
    > UrgentBox-6 > UrgentBox-3 > UrgentBox-1
    > ExtraCube-1:30 > UrgentCube-2:15
    > Major
    > DailyChip > DailyResource
    > Extra-0:20 > Extra-0:30 > Extra-1:00 > Extra-1:30 > Extra-2:00
    > NightOil > NightCube
    > shortest
    """
}
