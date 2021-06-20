from datetime import datetime, timedelta

from module.base.decorator import cached_property
from module.base.utils import ensure_time
from module.guild.assets import GUILD_RED_DOT
from module.guild.lobby import GuildLobby
from module.guild.logistics import GuildLogistics, RECORD_OPTION_LOGISTICS, RECORD_SINCE_LOGISTICS
from module.guild.operations import GuildOperations, RECORD_OPTION_DISPATCH, RECORD_SINCE_DISPATCH
from module.logger import logger
from module.ui.ui import page_guild

GUILD_RECORD = ('RewardRecord', 'guild')


class RewardGuild(GuildLobby, GuildLogistics, GuildOperations):
    @cached_property
    def guild_interval(self):
        return int(ensure_time(self.config.GUILD_INTERVAL, precision=3) * 60)

    def guild_interval_reset(self):
        """ Call this method after guild run executed """
        del self.__dict__['guild_interval']

    def handle_guild(self):
        """
        ALAS handler function for guild reward loop

        Returns:
            bool: If executed

        Pages:
            in: page_main
            out: page_main
        """
        if not self.config.ENABLE_GUILD_LOGISTICS and not self.config.ENABLE_GUILD_OPERATIONS:
            return False

        now = datetime.now()
        guild_record = datetime.strptime(self.config.config.get(*GUILD_RECORD), self.config.TIME_FORMAT)
        update = guild_record + timedelta(seconds=self.guild_interval)
        attr = f'{GUILD_RECORD[0]}_{GUILD_RECORD[1]}'
        logger.attr(f'{attr}', f'Record time: {guild_record}')
        logger.attr(f'{attr}', f'Next update: {update}')
        if not now > update:
            return False
        if not self.appear(GUILD_RED_DOT, offset=(30, 30)):
            logger.info('Guild red dot not appears, skip current check')
            self.config.record_save(option=GUILD_RECORD)
            return False

        self.ui_ensure(page_guild)

        # Lobby
        self.guild_lobby()

        # Logistics
        if self.config.ENABLE_GUILD_LOGISTICS \
                and not self.config.record_executed_since(option=RECORD_OPTION_LOGISTICS, since=RECORD_SINCE_LOGISTICS):
            # Save record when guild mission has been finished this week
            # If finished, only need to check guild logostics once a day
            # If not finished, check it in every guild reward
            if self.guild_logistics():
                self.config.record_save(option=RECORD_OPTION_LOGISTICS)

        # Operation
        if self.config.ENABLE_GUILD_OPERATIONS \
                and not self.config.record_executed_since(option=RECORD_OPTION_DISPATCH, since=RECORD_SINCE_DISPATCH):
            # Check guild operation 4 times a day
            self.guild_operations()

        self.guild_interval_reset()
        self.config.record_save(option=GUILD_RECORD)
        self.ui_goto_main()
        return True
