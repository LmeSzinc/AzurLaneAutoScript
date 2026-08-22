"""Phase 4D gate: registry families must equal the legacy constants and stay complete.

Legacy constants lived in module/config/config_updater.py L32-39 (MAINS/EVENTS/
GEMS_FARMINGS/RAIDS/WAR_ARCHIVES/COALITIONS/MARITIME_ESCORTS/HOSPITAL). This
script asserts family_tasks() derives exactly those sets from TASK_REGISTRY.
"""

import sys

sys.path.insert(0, ".")

import inflection

from module.tasks.registry import TASK_BY_COMMAND, TASK_FAMILIES, TASK_REGISTRY, family_tasks

LEGACY = {
    'main': ['Main', 'Main2', 'Main3'],
    'event': ['Event', 'Event2', 'EventA', 'EventB', 'EventC', 'EventD', 'EventSp'],
    'gems': ['GemsFarming'],
    'raid': ['Raid', 'RaidDaily'],
    'war_archives': ['WarArchives'],
    'coalition': ['Coalition', 'CoalitionSp'],
    'maritime': ['MaritimeEscort'],
    'hospital': ['Hospital'],
}

errors = []
for family, legacy in LEGACY.items():
    # Membership equality only; family_tasks order is registry declaration order.
    if sorted(family_tasks(family)) != sorted(legacy):
        errors.append(f"{family}: {family_tasks(family)} != {legacy}")
# completeness: every registry name resolves via underscore alias
for name in TASK_REGISTRY:
    if TASK_BY_COMMAND.get(inflection.underscore(name)) != name:
        errors.append(f"alias broken: {name}")
# every tagged task appears in exactly one family, untagged tasks excluded
tagged = [t for f in TASK_FAMILIES for t in family_tasks(f)]
if len(tagged) != len(set(tagged)):
    errors.append("duplicate family membership")
for name in TASK_REGISTRY:
    entry = TASK_REGISTRY[name]
    if (entry.family is not None) != (name in tagged):
        errors.append(f"family tag mismatch: {name}")

if errors:
    print("FAMILIES: FAIL")
    for e in errors:
        print(" ", e)
    sys.exit(1)
print(f"FAMILIES: OK ({len(TASK_FAMILIES)} families, {len(tagged)} tagged tasks)")
