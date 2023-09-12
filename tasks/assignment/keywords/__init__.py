import tasks.assignment.keywords.entry as KEYWORDS_ASSIGNMENT_ENTRY
import tasks.assignment.keywords.group as KEYWORDS_ASSIGNMENT_GROUP
from tasks.assignment.keywords.classes import AssignmentEntry, AssignmentGroup

KEYWORDS_ASSIGNMENT_GROUP.Character_Materials.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Nine_Billion_Names,
    KEYWORDS_ASSIGNMENT_ENTRY.Destruction_of_the_Destroyer,
    KEYWORDS_ASSIGNMENT_ENTRY.Winter_Soldiers,
    KEYWORDS_ASSIGNMENT_ENTRY.Born_to_Obey,
    KEYWORDS_ASSIGNMENT_ENTRY.Root_Out_the_Turpitude,
    KEYWORDS_ASSIGNMENT_ENTRY.Fire_Lord_Inflames_Blades_of_War,
)
KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Nameless_Land_Nameless_People,
    KEYWORDS_ASSIGNMENT_ENTRY.Akashic_Records,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Invisible_Hand,
)
KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Abandoned_and_Insulted,
    KEYWORDS_ASSIGNMENT_ENTRY.Spring_of_Life,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Land_of_Gold,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Blossom_in_the_Storm,
    KEYWORDS_ASSIGNMENT_ENTRY.Legend_of_the_Puppet_Master,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Wages_of_Humanity,
)
for group in (
        KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
        KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
        KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
):
    for entry in group.entries:
        assert entry.group is None
        entry.group = group
