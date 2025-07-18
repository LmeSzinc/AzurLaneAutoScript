import os
import re
import shutil
from datetime import datetime
from typing import List

from cached_property import cached_property
from tqdm import tqdm

from module.base.timer import timer
from module.config.config_updater import ConfigGenerator, ConfigUpdater
from module.logger import logger

SERVER_INDEXS = {
    'cn': 3,
    'en': 4,
    'jp': 5,
    'tw': 6
}

class WarArchivesUpdater:
    aired_date = None
    event = None

    def __init__(self):
        self.cn, self.en, self.jp, self.tw = '-', '-', '-', '-'
        self.lines: List[str]

    def reset(self):
        self.cn, self.en, self.jp, self.tw = '-', '-', '-', '-'
        with open('./campaign/Readme.md', 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    @cached_property
    def lines(self):
        with open('./campaign/Readme.md', 'r', encoding='utf-8') as f:
            return f.readlines()

    @cached_property
    def latest_event_cn(self):
        for text in self.lines[::-1]:
            if not re.search(r'^\|.+\|$', text):
                # not a table line
                continue
            elif re.search(r'^.*\-{3,}.*$', text):
                # is a delimiter line
                continue
            else:
                latest = [x.strip() for x in text.strip('| \n').split('|')]
                if latest[SERVER_INDEXS['cn']] != '-':
                    return re.search(r'\d{8}', latest[1]).group(0)
        return re.search(r'\d{8}', self.lines[-1].strip('| \n').split('|')[1].strip()).group(0)

    def event_name_to_time(self, name):
        """
        Args:
            name (str): event name, such as '虹彩的终幕曲'

        Returns:
            str: event time, such as '20220428'
                 If cannot find, return the time of the latest event
        """
        if len(name) == 8 and re.search(r'\d{8}', name):
            return name
        for text in self.lines:
            if name in text:
                return re.search(r'\d{8}', text.strip('| \n').split('|')[1].strip()).group(0)
        return self.latest_event_cn

    def event_time_to_name(self, time):
        """
        Args:
            time (str): event time, such as '20220428'

        Returns:
            str: event name in EN server, such as 'Rondo at Rainbow's End'
                 If cannot find, return the name of the latest event
        """
        for text in self.lines:
            if not re.search(r'^\|.+\|$', text):
                # not a table line
                continue
            elif re.search(r'^.*\-{3,}.*$', text):
                # is a delimiter line
                continue
            else:
                line = [x.strip() for x in text.strip('| \n').split('|')]
                if time in line[1]:
                    return line[SERVER_INDEXS['en']]
        return self.lines[-1].strip('| \n').split('|')[SERVER_INDEXS['en']].strip()

    def create_campaign_files(self, old_path, new_path):
        if os.path.exists(old_path):
            if not os.path.exists(new_path):
                logger.info(f'Creating files at {new_path}')
                shutil.copytree(old_path, new_path, ignore=shutil.ignore_patterns('sp.py'))
            else:
                logger.info(f'Directory already exists: {new_path}, skip creating files')
                sp_path = os.path.join(new_path, 'sp.py')
                if os.path.exists(sp_path):
                    logger.info(f'Removing sp files')
                    os.remove(sp_path)
                return False
        else:
            logger.warning(f'No such directory: {old_path}')
            return False
        return True

    def modify_campaign_files(self, old_path, new_path):
        if os.path.exists(old_path) and os.path.exists(new_path):
            files = os.listdir(new_path)
            for file_name in tqdm(files):
                if os.path.splitext(file_name)[-1] == '.py':
                    self.modify_single_campaign_file(os.path.join(new_path, file_name))
        else:
            logger.warning('No such directory, skip modifying files')

    def modify_single_campaign_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        pattern = 'from module.campaign.campaign_base import CampaignBase'
        replace = 'from ..campaign_war_archives.campaign_base import CampaignBase'
        modify = False
        for line in lines:
            modified_line = line.replace(pattern, replace)
            if line != modified_line:
                modify = True
            new_lines.append(modified_line)

        if modify:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        else:
            logger.info(f'No changes, skip modifying file {os.path.basename(file_path)}')

    @timer
    def update_readme(self, aired_date, event):
        """
        Args:
            aired_date (str): war archives update time
            event (str): event time
        """
        insert = True
        for row, text in enumerate(self.lines):
            if f'war archives {event}' in text:
                insert = False
                break
            if not re.search(r'^\|.+\|$', text):
                # not a table line
                continue
            elif re.search(r'^.*\-{3,}.*$', text):
                # is a delimiter line
                continue
            else:
                line_entries = [x.strip() for x in text.strip('| \n').split('|')]
                if re.search(r'\d{8}', text) and event in line_entries[1]:
                    directory = line_entries[1].replace('event', 'war archives')
                    for server in SERVER_INDEXS.keys():
                        if line_entries[SERVER_INDEXS[server]] == '-':
                            continue
                        elif self.__getattribute__(server) == '-':
                            self.__setattr__(server, line_entries[SERVER_INDEXS[server]])
                if 'war archives' in text:
                    insert_row = row

        if insert:
            insert_event = [aired_date, directory, self.en] + \
                        [self.__getattribute__(server) for server in SERVER_INDEXS.keys()]
            self.lines.insert(insert_row + 1, '|' + '|'.join(insert_event) + '|\n')
            with open('./campaign/Readme.md', 'w', encoding='utf-8') as f:
                f.writelines(self.lines)

    @timer
    def update_campaign_files(self, event):
        """
        Args:
            event (str):
        """
        folder = './campaign'
        raw_directory = 'event_' + event + '_cn'
        directory = 'war_archives_' + event + '_cn'
        old_path = os.path.join(folder, raw_directory)
        new_path = os.path.join(folder, directory)
        self.create_campaign_files(old_path, new_path)
        self.modify_campaign_files(old_path, new_path)

    @timer
    def update_directory(self, event):
        """
        Args:
            event (str):
        """
        directory = 'war_archives_' + event + '_cn'
        name = self.event_time_to_name(event).replace('\'', '').replace('-', '_').replace(' ', '_').upper()
        file_path = './module/war_archives/dictionary.py'
        modify = True
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for row, text in enumerate(lines):
            if name in text:
                modify = False
                break
            if 'war_archives' in text:
                insert_row = row

        if modify:
            lines.insert(insert_row + 1, f'    \'{directory}\': TEMPLATE_{name},\n')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        else:
            logger.info('No changes, skip modifying dictionary.py')

    @timer
    def war_archives_update(self, aired_date=None, event=None):
        """
        Args:
            aired_date (str, list[str], None):
                use the YYYYMMDD format, such as '20220428',
                'today' or None for datetime.today()
            event (str, list[str], None):
                use the YYYYMMDD format, also can use the event name, such as ['雄鹰的叙事歌', '20220428']
                'recent' or None for the lastest event for CN server
        """
        if aired_date is None or aired_date == 'today':
            dates = [datetime.today().strftime("%Y%m%d")]
        elif isinstance(aired_date, str):
            dates = [aired_date]
        elif isinstance(aired_date, list):
            dates = [datetime.today().strftime("%Y%m%d") if d == 'today' else d for d in aired_date]
        else:
            logger.warning('Wrong Aired Date format')
            dates = []

        if event is None or event == 'recent':
            events = [self.latest_event_cn]
        elif isinstance(event, str):
            events = [self.event_name_to_time(event)]
        elif isinstance(event, list):
            events = [self.latest_event_cn if e == 'recent' else self.event_name_to_time(e) for e in event]
        else:
            logger.warning('Wrong Event format')
            events = []

        for aired_date, event in tqdm(zip(dates, events)):
            self.update_readme(aired_date, event)
            self.update_campaign_files(event)
            self.update_directory(event)
            self.reset()

    def run(self):
        self.war_archives_update(aired_date=self.aired_date, event=self.event)
        ConfigGenerator().generate()
        ConfigUpdater().update_file('template', is_template=True)

if __name__ == '__main__':
    # Date of update of war archives
    # input strings in YYYYMMDD format for war archives update time
    # use 'today' for today, use a list to input multiple values,
    # such as '20250717', 'today', ['20250619' , '20250717', 'today']
    WarArchivesUpdater.aired_date = '20250717'
    # Event name or date of update of war archives
    # input strings in YYYYMMDD format for event time, or input event name
    # use 'recent' for the latest CN enent, use a list to input multiple values,
    # such as '20220428', '虹彩的终幕曲', 'recent', ['雄鹰的叙事歌' , '20220428', 'recent']
    WarArchivesUpdater.event = '20220428'

    updater = WarArchivesUpdater()

    """
    Step 1:
        Run these code.
    """
    # Ensure running in Alas root folder
    os.chdir(os.path.join(os.path.dirname(__file__), '../'))
    updater.run()
