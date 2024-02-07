import typing as t

from dev_tools.keywords.base import GenerateKeyword
from module.base.decorator import cached_property
from module.config.utils import deep_get


class GenerateMapPlane(GenerateKeyword):
    output_file = './tasks/map/keywords/plane.py'

    @cached_property
    def data(self):
        return self.read_file('./ExcelOutput/AreaMapConfig.json')

    def iter_planes(self) -> t.Iterable[dict]:
        for plane_id, data in self.data.items():
            plane_id = int(plane_id)
            world_id = int(str(plane_id)[-5])
            sort_id = int(deep_get(data, 'MenuSortID', 0))
            text_id = deep_get(data, 'Name.Hash')
            yield dict(
                text_id=text_id,
                world_id=world_id,
                plane_id=plane_id,
                sort_id=sort_id,
            )

    def iter_keywords(self) -> t.Iterable[dict]:
        """
        1010201
             ^^ floor
           ^^ plane
          ^ world
        """
        def to_id(name):
            return self.find_keyword(name, lang='cn')[0]

        domains = ['黑塔的办公室', '锋芒崭露']
        for index, domain in enumerate(domains):
            yield dict(
                text_id=to_id(domain),
                world_id=-1,
                plane_id=index + 1,
            )
        domains = ['区域-战斗', '区域-事件', '区域-遭遇', '区域-休整', '区域-精英', '区域-首领', '区域-交易']
        for index, domain in enumerate(domains):
            yield dict(
                text_id=to_id(domain),
                world_id=-2,
                plane_id=index + 1,
            )

        keywords = sorted(self.iter_planes(), key=lambda x: (x['world_id'], x['sort_id']))
        for keyword in keywords:
            keyword.pop('sort_id')
            yield keyword

    def convert_name(self, text: str, keyword: dict) -> str:
        text = super().convert_name(text, keyword=keyword)
        text = text.replace('_', '')

        from tasks.map.keywords import MapWorld
        world = MapWorld.find_world_id(keyword['world_id'])
        if world is None:
            if text.startswith('Domain'):
                return f'Rogue_{text}'
            else:
                return f'Special_{text}'
        else:
            return f'{world.short_name}_{text}'
