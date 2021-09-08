import module.config.server as server


class ManualConfig:
    SERVER = server.server

    SCHEDULER_PRIORITY = """
    Restart
    > Research > Commission > Tactical > Dorm > Task
    > GuildLogistics > GuildOperation
    > Meowfficer > Gacha > Shop
    > OpsiObscure
    > Exercise > Daily > Hard > OpsiAsh
    > Sos > EventDaily > RaidDaily > WarArchieves
    > OpsiShop > OpsiDaily > OpsiFarm
    > Event > Raid > Main > GemsFarming
    """
