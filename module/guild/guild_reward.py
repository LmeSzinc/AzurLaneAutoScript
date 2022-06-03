from module.guild.lobby import GuildLobby
from module.guild.logistics import GuildLogistics
from module.guild.operations import GuildOperations
from module.ui.ui import page_guild, page_main


class RewardGuild(GuildLobby, GuildLogistics, GuildOperations):
    def run(self):
        """
        ALAS handler function for guild reward loop

        Returns:
            bool: If executed

        Pages:
            in: page_main
            out: page_main
        """
        if (
            not self.config.GuildLogistics_Enable
            and not self.config.GuildOperation_Enable
        ):
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.ui_ensure(page_guild)
        success = True

        # Lobby
        self.guild_lobby()

        # Logistics
        if self.config.GuildLogistics_Enable:
            success &= self.guild_logistics()

        # Operation
        if self.config.GuildOperation_Enable:
            success &= self.guild_operations()

        self.ui_goto(page_main)

        # Scheduler
        if success:
            self.config.task_delay(server_update=True)
        else:
            self.config.task_delay(success=False, server_update=True)
