import tasks.assignment.keywords.entry as KEYWORDS_ASSIGNMENT_ENTRY
import tasks.assignment.keywords.group as KEYWORDS_ASSIGNMENT_GROUP
import tasks.assignment.keywords.event_entry as KEYWORDS_ASSIGNMENT_EVENT_ENTRY
import tasks.assignment.keywords.event_group as KEYWORDS_ASSIGNMENT_EVENT_GROUP
from tasks.assignment.keywords.classes import *

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
KEYWORDS_ASSIGNMENT_EVENT_GROUP.Space_Station_Task_Force.entries = (
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Repulsion_Bridge_Errors,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Meal_Delivery_Robot_Check_Up,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Noise_Complaint,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Interior_Temperature_Modulator,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Researcher_Health_Reports,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Confidential_Investigation,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Borrowed_Equipment,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Booking_System,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Non_Digital_Documents,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Drip_Feed_Errors,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Pet_Movement_Route_Planning,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Food_Improvement_Plan,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Curio_Distribution,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Super_Urgent_Waiting_Online,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Ventilation_Problem,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Unstable_Connection,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Chronology_Checks,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Supply_Chain_Management,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Malicious_Occupation_of_Public_Space,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Uniform_Material,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Virus_Re_creation_Report,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Abnormal_Signal,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Flexible_Working_Approval,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Lighting_Issue,
)
for group in (
        KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
        KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
        KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
        KEYWORDS_ASSIGNMENT_EVENT_GROUP.Space_Station_Task_Force,
):
    for entry in group.entries:
        assert entry.group is None
        entry.group = group
