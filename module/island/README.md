# Island Season List

The `/module/island` directory contains island automation and its generated data.
[data.py](data.py) stores permanent definitions; [season_data.py](season_data.py)
stores seasonal activation and server overrides.

**Island > IslandGeneral > Season** is locked to the latest season listed for
the selected server, like campaign events. All island tasks and the production
planner share this setting. The table below supplies the namespaces and
localized labels.
This release list is maintained independently of `island_extractor`.

As in [the campaign list](../../campaign/Readme.md), one content namespace is
shared across servers. A later server release uses the same namespace, and the
date in that namespace can differ from the aired date.

**Aired Date** The season's start date on the servers listed in that row.

**End Date** The end date for that release. CN/EN/JP share the CN date; TW uses
its own season boundary.

**Namespace** The shared key in `DIC_ISLAND_SEASON`.

**Season Name** The English season name, or the CN name if it has not aired in EN.

**CN, EN, JP, TW** Localized season names. Use `-` when that server is not part of
the release shown in the row.

| Aired Date | End Date | Namespace | Season Name | CN | EN | JP | TW |
| :--------- | :------- | :-------- | :---------- | :-- | :-- | :-- | :-- |
| 20250929 | 20260205 | season_20251106_cn | Development Season I - Let's Get Started! | 岛屿开发季I——启动时刻！ | Development Season I - Let's Get Started! | 開発シーズンⅠ | - |
| 20260205 | 20260507 | season_20260205_cn | Development Season II - Spring Merrymaking | 岛屿开发季II——春日闲趣 | Development Season II - Spring Merrymaking | 開発シーズンⅡ | - |
| 20260507 | 20260806 | season_20260507_cn | Development Season Ⅲ – Summer Sojourn | 岛屿开发季III——夏日悠游 | Development Season Ⅲ – Summer Sojourn | 開発シーズンⅢ | - |
| 20260806 | 20261105 | season_20260806_cn | Island Planner Season IV - Tales from Autumn | 岛屿开发季IV——秋日絮语 | Island Planner Season IV - Tales from Autumn | 開発シーズンⅣ | - |
| 20260820 | 20261119 | season_20260806_cn | Island Planner Season IV - Tales from Autumn | - | - | - | 島嶼開發季I——秋日絮語 |
| 20261105 | 20270201 | season_20261105_cn | Island Planner Season V – Winter Wanderlust | 岛屿开发季V——冬日漫行 | Island Planner Season V – Winter Wanderlust | 離島開発シーズンⅤ――冬日漫々 | - |
