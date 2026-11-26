from module.eventstory.eventstory_base import EventStoryBase
from module.ui.ui import UI


class EventStory(UI):
    def run(self):
        if self.config.cross_get('Coalition.Campaign.Event') == 'coalition_20261124':
            from module.eventstory.eventstory_20261124 import EventStory20261124
            event = EventStory20261124(config=self.config, device=self.device)
            event.run()
            return

        event = EventStoryBase(config=self.config, device=self.device)
        event.run()
