PORT_SHOP_PRESET = {
    #   line:
    #   1: Logger, PurpleCoins and T4 items
    #   2: T3 items
    #   3: ActionPoint
    #   4: META material
    #   5-end: Rubbish

    'max_benefit': """
        Logger > PurpleCoins >
        PlatePartT4 > PlatePartT3 > PlateWildT3 >
        GearPlanT4 > GearReportT4 > GearPlanT3 > GearReportT3 >
        BoxMatT3
    """,
    'max_benefit_meta': """
        Logger > PurpleCoins >
        BookMETA > RiggingMETA >
        PlatePartT4 > PlatePartT3 > PlateWildT3 >
        GearPlanT4 > GearReportT4 > GearPlanT3 > GearReportT3 >
        BoxMatT3 >
        ActionPoint
    """,
    'max_benefit_exploration':"""
        Logger > PurpleCoins >
        Tuning > EnergyStorageDevice >
        ActionPoint > RepairPack >
        PlatePartT4 > PlatePartT3 > PlateWildT3 >
        GearPlanT4 > GearReportT4 > GearPlanT3 > GearReportT3 >
        BoxMatT3
    """,
    'all': """
        Logger > PurpleCoins >
        Tuning > EnergyStorageDevice >
        PlatePartT4 > PlatePartT3 > PlateWildT3 >
        GearPlanT4 > GearReportT4 > GearPlanT3 > GearReportT3 >
        BoxMatT3 >
        BookMETA > RiggingMETA >
        ActionPoint > RepairPack
    """
}