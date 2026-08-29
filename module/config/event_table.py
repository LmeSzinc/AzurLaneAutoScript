"""Event table parsing/insertion (split from config_updater.py, Phase 5.1)."""
import re

from module.base.decorator import cached_property
from module.base.timer import timer
from module.config.deep import deep_get, deep_set
from module.config.redirect_utils.utils import *  # noqa: F403  (re-export facade)
from module.config.utils import *  # noqa: F403  (re-export facade)
from module.tasks.registry import family_tasks

ARCHIVES_PREFIX = {
    'cn': '档案 ',
    'en': 'archives ',
    'jp': '檔案 ',
    'tw': '檔案 '
}


class Event:
    def __init__(self, text):
        self.date, self.directory, self.name, self.cn, self.en, self.jp, self.tw \
            = [x.strip() for x in text.strip('| \n').split('|')]

        self.directory = self.directory.replace(' ', '_')
        self.cn = self.cn.replace('、', '')
        self.en = self.en.replace(',', '').replace('\'', '').replace('\\', '')
        self.jp = self.jp.replace('、', '')
        self.tw = self.tw.replace('、', '')
        self.is_war_archives = self.directory.startswith('war_archives')
        self.is_raid = self.directory.startswith('raid_')
        self.is_coalition = self.directory.startswith('coalition_')
        for server in ARCHIVES_PREFIX:
            if self.__getattribute__(server) == '-':
                self.__setattr__(server, None)
            else:
                if self.is_war_archives:
                    self.__setattr__(server, ARCHIVES_PREFIX[server] + self.__getattribute__(server))

    def __str__(self):
        return self.directory

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __hash__(self):
        return hash(str(self))


class EventTableMixin:
    @cached_property
    @timer
    def event(self):
        """
        Returns:
            list[Event]: From latest to oldest
        """

        def calc_width(text):
            return len(text) + len(re.findall(
                r'[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff、！（）]', text))

        lines = []
        data_lines = []
        data_widths = []
        column_width = [4] * 7  # `:---`
        events = []
        with open('./campaign/Readme.md', encoding='utf-8') as f:
            for text in f.readlines():
                if not re.search(r'^\|.+\|$', text):
                    # not a table line
                    lines.append(text)
                elif re.search(r'^.*\-{3,}.*$', text):
                    # is a delimiter line
                    continue
                else:
                    line_entries = [x.strip() for x in text.strip('| \n').split('|')]
                    data_lines.append(line_entries)
                    data_width = [calc_width(string) for string in line_entries]
                    data_widths.append(data_width)
                    column_width = [max(l1, l2) for l1, l2 in zip(column_width, data_width)]
                    if re.search(r'\d{8}', text):
                        event = Event(text)
                        events.append(event)
        for i, (line, old_width) in enumerate(zip(data_lines, data_widths)):
            lines.append('| ' + ' | '.join([cell + ' ' * (width - length) for cell, width, length in zip(line, column_width, old_width)]) + ' |\n')
            if i == 0:
                lines.append('| ' + ' | '.join([':' + '-' * (width - 1) for width in column_width]) + ' |\n')
        with open('./campaign/Readme.md', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return events[::-1]

    def insert_event(self):
        """
        Insert event information into `self.args`.

        ./campaign/Readme.md -----+
                                  v
                   args.json -----+-----> args.json

        Phase 4D: table-driven. Latest-date rule per (server, family) mirrors
        the legacy hasattr-based per-server latest date tracking.
        """
        rules = [
            (lambda e: e.is_raid, 'raid', 'raid'),
            (lambda e: e.is_war_archives, 'war_archives', None),
            (lambda e: e.is_coalition, 'coalition', 'coalition'),
            (lambda e: True, 'event', 'event'),
        ]
        latest: dict[tuple[str, str], int] = {}
        for server in ARCHIVES_PREFIX:
            for event in self.event:
                name = event.__getattribute__(server)
                if not name:
                    continue
                for predicate, _family, _latest_key in rules:
                    if predicate(event):
                        break
                if _latest_key is not None:
                    key = (server, _latest_key)
                    if key not in latest:
                        latest[key] = int(event.date)
                    elif int(event.date) != latest[key]:
                        continue
                if _family == 'event':
                    tasks = family_tasks('event') + family_tasks('gems')
                else:
                    tasks = family_tasks(_family)
                for task in tasks:

                    def insert(key, server=server, event=event):
                        opts = deep_get(self.args, keys=f'{key}.Campaign.Event.option_{server}', default=[])
                        if event not in opts:
                            opts.append(event)
                        deep_set(self.args, keys=f'{key}.Campaign.Event.option_{server}', value=opts)

                    insert(task)

        for task in (family_tasks('event') + family_tasks('gems') + family_tasks('war_archives')
                     + family_tasks('raid') + family_tasks('coalition')):
            latest = {}
            for server in ARCHIVES_PREFIX:
                latest[server] = deep_get(self.args, keys=f'{task}.Campaign.Event.option_{server}', default=[])
            options = set().union(*latest.values())
            options = sorted([option for option in options if option != 'campaign_main'])
            if task not in family_tasks('war_archives'):
                deep_set(self.args, keys=f'{task}.Campaign.Event.option_bold', value=options)
            deep_set(self.args, keys=f'{task}.Campaign.Event.option', value=options)
