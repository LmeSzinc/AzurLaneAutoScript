from functools import cache
from typing import Iterable

from dev_tools.keywords.base import UI_LANGUAGES, GenerateKeyword
from module.config.utils import deep_get


@cache
def get_assignment_entry_data():
    """
    Returns:
        dict: key - assignment text_id
              value - text_id of reward items
    """
    expedition_namehash_to_id = {
        deep_get(expedition, 'Name.Hash'): deep_get(expedition, 'ExpeditionID')
        for expedition in GenerateKeyword.read_file('./ExcelOutput/ExpeditionData.json').values()
    }
    expedition_id_to_reward_id = {
        deep_get(expedition, '4.2.ExpeditionID'): deep_get(expedition, '4.2.RewardID')
        for expedition in GenerateKeyword.read_file('./ExcelOutput/ExpeditionReward.json').values()
    }
    reward_id_to_item_ids = {
        deep_get(reward, 'RewardID'): [
            v for k, v in reward.items()
            if k.startswith('ItemID')
        ]
        for reward in GenerateKeyword.read_file('./ExcelOutput/RewardData.json').values()
    }
    item_id_to_namehash = {
        deep_get(item, 'ID'): deep_get(item, 'ItemName.Hash')
        for item in GenerateKeyword.read_file('./ExcelOutput/ItemConfig.json').values()
    }
    item_name_remap = {
        '旅情见闻': '角色经验材料',
        '稀薄以太': '光锥经验材料'
    }
    ret = dict()
    for expedition_namehash, expedition_id in expedition_namehash_to_id.items():
        reward_id = expedition_id_to_reward_id[expedition_id]
        item_ids = reward_id_to_item_ids[reward_id]
        item_names = [item_id_to_namehash[x] for x in item_ids]
        if len(item_names) == 1:
            item = GenerateKeyword.find_keyword(item_names[0], lang='cn')[1]
            if item in item_name_remap:
                item_names = [GenerateKeyword.find_keyword(
                    item_name_remap[item], lang='cn')[0]]
        ret[expedition_namehash] = item_names
    return ret


class GenerateAssignment(GenerateKeyword):
    def generate(self):
        GenerateAssignmentGroup()()
        GenerateAssignmentEntry()()
        GenerateAssignmentEventGroup()()
        GenerateAssignmentEventEntry()()
        GenerateAssignmentEntryDetailed()()


class GenerateAssignmentGroup(GenerateKeyword):
    output_file = './tasks/assignment/keywords/group.py'

    def iter_keywords(self) -> Iterable[dict]:
        for group in self.read_file('./ExcelOutput/ExpeditionGroup.json').values():
            yield dict(text_id=deep_get(group, 'Name.Hash'))


class GenerateAssignmentEntry(GenerateKeyword):
    output_file = './tasks/assignment/keywords/entry.py'

    def iter_keywords(self) -> Iterable[dict]:
        for k in get_assignment_entry_data().keys():
            yield dict(text_id=k)


class GenerateAssignmentEntryDetailed(GenerateKeyword):
    output_file = './tasks/assignment/keywords/entry_detailed.py'

    def iter_keywords(self) -> Iterable[dict]:
        for assignment_id, reward_ids in get_assignment_entry_data().items():
            yield dict(
                text_id=assignment_id,
                reward_ids=reward_ids
            )

    def iter_rows(self) -> Iterable[dict]:
        for keyword in super().iter_rows():
            reward_ids = keyword.pop('reward_ids')
            for lang in UI_LANGUAGES:
                assignment_name = keyword[lang]
                reward_name = ' & '.join(
                    self.find_keyword(reward_id, lang=lang)[1]
                    for reward_id in reward_ids
                )
                name_format = '{reward_name} ({assignment_name})' if lang in {
                    'en', 'es'} else '{reward_name}（{assignment_name}）'
                keyword[lang] = name_format.format(
                    reward_name=reward_name,
                    assignment_name=assignment_name
                )
            yield keyword


class GenerateAssignmentEventGroup(GenerateKeyword):
    output_file = './tasks/assignment/keywords/event_group.py'

    def iter_keywords(self) -> Iterable[dict]:
        yield dict(text_id=self.find_keyword('空间站特派', lang='cn')[0])


class GenerateAssignmentEventEntry(GenerateKeyword):
    output_file = './tasks/assignment/keywords/event_entry.py'

    def iter_keywords(self) -> Iterable[dict]:
        for expedition in self.read_file('./ExcelOutput/ActivityExpedition.json').values():
            yield dict(text_id=deep_get(expedition, 'Name.Hash'))


if __name__ == "__main__":
    from dev_tools.keywords.base import TextMap
    TextMap.DATA_FOLDER = '../StarRailData'
    GenerateAssignment()()
