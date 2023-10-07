from tasks.rogue.keywords import KEYWORDS_ROGUE_EVENT_TITLE, KEYWORDS_ROGUE_EVENT_OPTION

# TODO: events that only come up in Swarm Disaster (寰宇蝗灾)
STRATEGY_COMMON = {
    KEYWORDS_ROGUE_EVENT_TITLE.Rest_Area: [
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_1_Curio,
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_1_star_Blessing,
        KEYWORDS_ROGUE_EVENT_OPTION.Enhance_2_random_Blessings
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Shopping_Channel: [
        KEYWORDS_ROGUE_EVENT_OPTION.A_lotus_that_can_sing_the_Happy_Birthday_song,
        KEYWORDS_ROGUE_EVENT_OPTION.A_mechanical_box,
        KEYWORDS_ROGUE_EVENT_OPTION.A_box_of_expired_doughnuts
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Interactive_Arts: [
        KEYWORDS_ROGUE_EVENT_OPTION.Action,
        KEYWORDS_ROGUE_EVENT_OPTION.Musical
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.I_O_U_Dispenser: [
        KEYWORDS_ROGUE_EVENT_OPTION.You_re_not_a_reliable_investment_manager,
        KEYWORDS_ROGUE_EVENT_OPTION.I_hate_this_era,
        KEYWORDS_ROGUE_EVENT_OPTION.I_don_t_want_anything_This_is_very_nihilistic,
        KEYWORDS_ROGUE_EVENT_OPTION.I_don_t_need_it
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Statue: [
        KEYWORDS_ROGUE_EVENT_OPTION.Believe_in_them_with_pure_devotion,
        KEYWORDS_ROGUE_EVENT_OPTION.Discard_the_statue_Be_decisive
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Unending_Darkness: [
        KEYWORDS_ROGUE_EVENT_OPTION.Fight_the_pull,
        KEYWORDS_ROGUE_EVENT_OPTION.Head_into_the_darkness,
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Cosmic_Merchant_Part_1: [
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_metal_Wish_In_A_Bottle,
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_silver_ore_Wish_In_A_Bottle_18,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_18
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Cosmic_Con_Job_Part_2: [
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_an_amber_Wish_In_A_Bottle_19,
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_supernium_Wish_In_A_Bottle_19,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_19
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Cosmic_Altruist_Part_3: [
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_diamond_box_20,
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_an_ore_box_20,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_20
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Make_A_Wish: [
        KEYWORDS_ROGUE_EVENT_OPTION.Exchange_for_a_3_star_Blessing,
        KEYWORDS_ROGUE_EVENT_OPTION.Exchange_for_a_2_star_Blessing,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_33
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Robot_Sales_Terminal: [
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_1_3_star_Blessing,
        KEYWORDS_ROGUE_EVENT_OPTION.Purchase_a_1_2_star_Blessing,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_34
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Insights_from_the_Universal_Dancer: [
        KEYWORDS_ROGUE_EVENT_OPTION.Tell_fortune,
        KEYWORDS_ROGUE_EVENT_OPTION.Refuse_invitation
    ]
}
STRATEGY_FIGHT = {
    KEYWORDS_ROGUE_EVENT_TITLE.Insect_Nest: [
        KEYWORDS_ROGUE_EVENT_OPTION.Go_deeper_into_the_insect_nest,
        KEYWORDS_ROGUE_EVENT_OPTION.Hug_it,
        KEYWORDS_ROGUE_EVENT_OPTION.Stop_at_the_entrance_of_the_nest,
        KEYWORDS_ROGUE_EVENT_OPTION.Wait_for_them
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Three_Little_Pigs: [
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_14,
        KEYWORDS_ROGUE_EVENT_OPTION.Play_a_bit_with_Sequence_Trotters
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Kindling_of_the_Self_Annihilator: [
        KEYWORDS_ROGUE_EVENT_OPTION.Accept_the_flames_of_Self_destruction_and_destroy_the_black_box,
        KEYWORDS_ROGUE_EVENT_OPTION.Refuse_17
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Societal_Dreamscape: [
        KEYWORDS_ROGUE_EVENT_OPTION.Swallow_the_other_fish_eye_and_continue_to_enjoy_the_massage,
        KEYWORDS_ROGUE_EVENT_OPTION.Return_to_work
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Bounty_Hunter: [
        KEYWORDS_ROGUE_EVENT_OPTION.Give_him_the_fur_you_re_wearing,
        KEYWORDS_ROGUE_EVENT_OPTION.Walk_away_25
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Implement_of_Error: [
        KEYWORDS_ROGUE_EVENT_OPTION.Pick_an_Error_Code_Curio,
        KEYWORDS_ROGUE_EVENT_OPTION.Leave_26
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.We_Are_Cowboys: [
        KEYWORDS_ROGUE_EVENT_OPTION.Protect_the_cowboy_final_honor,
        KEYWORDS_ROGUE_EVENT_OPTION.Pay
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Nildis: [
        KEYWORDS_ROGUE_EVENT_OPTION.Flip_the_card,
        KEYWORDS_ROGUE_EVENT_OPTION.Give_up
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Rock_Paper_Scissors: [
        KEYWORDS_ROGUE_EVENT_OPTION.Fight_for_the_0_63_chance,
        KEYWORDS_ROGUE_EVENT_OPTION.Pick_the_100_security
    ],
    KEYWORDS_ROGUE_EVENT_TITLE.Tavern: [
        KEYWORDS_ROGUE_EVENT_OPTION.Fight_both_together,
        KEYWORDS_ROGUE_EVENT_OPTION.Challenge_Mr_France_security_team,
        KEYWORDS_ROGUE_EVENT_OPTION.Challenge_the_burly_Avila_mercenary_company
    ]
}
STRATEGY_LEAVE = dict()
for k, v in STRATEGY_FIGHT.items():
    STRATEGY_LEAVE[k] = list(reversed(v))
STRATEGIES = {
    'leave': {**STRATEGY_LEAVE, **STRATEGY_COMMON},
    'fight': {**STRATEGY_FIGHT, **STRATEGY_COMMON}
}
