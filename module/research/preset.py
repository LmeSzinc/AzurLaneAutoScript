FILTER_STRING_SHORTEST = '0.5 > 1 > 1.5 > 2 > 2.5 > 3 > 4 > 5 > 6 > 8 > 10 > 12'
FILTER_STRING_CHEAPEST = 'Q1 > Q2 > T3 > T4 > Q4 > C6 > T6 > C8 > C12 > G1.5 > D2.5 > G2.5 > D5 > Q0.5 > G4 > D8 > H1 > H2 > H0.5 > D0.5 > H4'
DICT_FILTER_PRESET = {
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 153.41706666666678
    # Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
    'series_6_203_only_cube': """
        S6-Q0.5 > S6-DR0.5 > S6-PRY0.5 > Q0.5 > S6-Q4 > S6-Q2 > S6-Q1 > 0.5
        > S6-E-315 > S6-G1.5 > S6-G4 > Q1 > reset > S6-H1 > H1 > 1 > S6-E-031
        > S6-DR2.5 > S6-PRY2.5 > S6-G2.5 > G1.5 > 1.5 > Q2 > E2 > S6-H2 > H2
        > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S6-DR5 > S6-PRY5 > Q4 > G4
        > S6-H4 > H4 > 4 > S6-C6 > DR5 > PRY5 > 5 > S6-DR8 > S6-PRY8 > S6-C8
        > C6 > 6 > S6-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 161.37177965277806
    # Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
    'series_6_203_only': """
        S6-Q0.5 > S6-PRY0.5 > S6-DR0.5 > Q0.5 > S6-Q4 > S6-Q2 > S6-Q1 > 0.5
        > S6-E-315 > S6-G4 > S6-G1.5 > Q1 > 1 > S6-E-031 > S6-DR2.5 > reset
        > S6-G2.5 > S6-PRY2.5 > G1.5 > 1.5 > Q2 > E2 > 2 > DR2.5 > PRY2.5
        > G2.5 > 2.5 > S6-DR5 > S6-PRY5 > Q4 > G4 > 4 > S6-C6 > DR5 > PRY5
        > 5 > S6-DR8 > S6-PRY8 > S6-C8 > C6 > 6 > DR8 > PRY8 > C8 > 8
        > S6-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 124.67622465277958
    # Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
    'series_6_blueprint_203_cube': """
        S6-DR0.5 > S6-Q0.5 > S6-PRY0.5 > 0.5 > S6-DR2.5 > S6-Q1 > S6-Q2
        > S6-H1 > S6-E-315 > S6-G1.5 > reset > S6-Q4 > S6-G4 > S6-H2 > Q1
        > H1 > 1 > S6-G2.5 > S6-DR5 > S6-PRY2.5 > G1.5 > 1.5 > S6-E-031
        > S6-DR8 > Q2 > E2 > H2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S6-H4
        > S6-PRY5 > Q4 > G4 > H4 > 4 > S6-C6 > S6-PRY8 > DR5 > PRY5 > 5 > C6
        > 6 > S6-C8 > DR8 > PRY8 > C8 > 8 > S6-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 143.56399131945145
    # Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
    'series_6_blueprint_203': """
        S6-DR0.5 > S6-PRY0.5 > S6-Q0.5 > S6-H0.5 > Q0.5 > S6-DR2.5
        > S6-G1.5 > S6-Q1 > S6-DR5 > 0.5 > S6-G4 > S6-Q2 > S6-PRY2.5 > reset
        > S6-DR8 > Q1 > 1 > S6-E-315 > S6-G2.5 > G1.5 > 1.5 > S6-E-031
        > S6-Q4 > Q2 > E2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S6-PRY5
        > S6-PRY8 > Q4 > G4 > 4 > S6-C6 > DR5 > PRY5 > 5 > C6 > 6 > S6-C8
        > S6-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 82.0121088194467
    # Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
    'series_6_blueprint_only_cube': """
        S6-DR0.5 > S6-PRY0.5 > S6-H0.5 > S6-H1 > S6-H2 > S6-DR2.5 > S6-DR5
        > 0.5 > S6-DR8 > reset > S6-H4 > S6-Q1 > Q1 > H1 > 1 > S6-G1.5 > G1.5
        > 1.5 > S6-G2.5 > S6-Q2 > S6-E-315 > S6-E-031 > Q2 > E2 > H2 > 2
        > S6-PRY2.5 > S6-G4 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S6-Q4 > Q4 > G4
        > H4 > 4 > S6-PRY5 > S6-PRY8 > S6-C6 > DR5 > PRY5 > 5 > C6 > 6
        > S6-C8 > S6-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 124.71616166666873
    # Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
    'series_6_blueprint_only': """
        S6-DR0.5 > S6-H0.5 > S6-PRY0.5 > S6-DR8 > S6-DR5 > S6-DR2.5
        > S6-G1.5 > S6-PRY2.5 > 0.5 > S6-G2.5 > S6-G4 > reset > S6-Q1 > Q1
        > 1 > S6-PRY5 > G1.5 > 1.5 > S6-Q2 > S6-E-031 > S6-E-315 > Q2 > E2
        > 2 > S6-PRY8 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S6-Q4 > Q4 > G4 > 4
        > S6-C6 > DR5 > PRY5 > 5 > C6 > 6 > S6-C8 > DR8 > PRY8 > C8 > 8
        > S6-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 153.41706666666678
    # Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
    'series_5_152_only_cube': """
        S5-Q0.5 > S5-DR0.5 > S5-PRY0.5 > Q0.5 > S5-Q4 > S5-Q2 > S5-Q1 > 0.5
        > S5-E-315 > S5-G1.5 > S5-G4 > Q1 > reset > S5-H1 > H1 > 1 > S5-E-031
        > S5-DR2.5 > S5-PRY2.5 > S5-G2.5 > G1.5 > 1.5 > Q2 > E2 > S5-H2 > H2
        > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S5-DR5 > S5-PRY5 > Q4 > G4
        > S5-H4 > H4 > 4 > S5-C6 > DR5 > PRY5 > 5 > S5-DR8 > S5-PRY8 > S5-C8
        > C6 > 6 > S5-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 161.37177965277806
    # Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
    'series_5_152_only': """
        S5-Q0.5 > S5-PRY0.5 > S5-DR0.5 > Q0.5 > S5-Q4 > S5-Q2 > S5-Q1 > 0.5
        > S5-E-315 > S5-G4 > S5-G1.5 > Q1 > 1 > S5-E-031 > S5-DR2.5 > reset
        > S5-G2.5 > S5-PRY2.5 > G1.5 > 1.5 > Q2 > E2 > 2 > DR2.5 > PRY2.5
        > G2.5 > 2.5 > S5-DR5 > S5-PRY5 > Q4 > G4 > 4 > S5-C6 > DR5 > PRY5
        > 5 > S5-DR8 > S5-PRY8 > S5-C8 > C6 > 6 > DR8 > PRY8 > C8 > 8
        > S5-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 124.67622465277958
    # Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
    'series_5_blueprint_152_cube': """
        S5-DR0.5 > S5-Q0.5 > S5-PRY0.5 > 0.5 > S5-DR2.5 > S5-Q1 > S5-Q2
        > S5-H1 > S5-E-315 > S5-G1.5 > reset > S5-Q4 > S5-G4 > S5-H2 > Q1
        > H1 > 1 > S5-G2.5 > S5-DR5 > S5-PRY2.5 > G1.5 > 1.5 > S5-E-031
        > S5-DR8 > Q2 > E2 > H2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S5-H4
        > S5-PRY5 > Q4 > G4 > H4 > 4 > S5-C6 > S5-PRY8 > DR5 > PRY5 > 5 > C6
        > 6 > S5-C8 > DR8 > PRY8 > C8 > 8 > S5-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 143.56399131945145
    # Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
    'series_5_blueprint_152': """
        S5-DR0.5 > S5-PRY0.5 > S5-Q0.5 > S5-H0.5 > Q0.5 > S5-DR2.5
        > S5-G1.5 > S5-Q1 > S5-DR5 > 0.5 > S5-G4 > S5-Q2 > S5-PRY2.5 > reset
        > S5-DR8 > Q1 > 1 > S5-E-315 > S5-G2.5 > G1.5 > 1.5 > S5-E-031
        > S5-Q4 > Q2 > E2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S5-PRY5
        > S5-PRY8 > Q4 > G4 > 4 > S5-C6 > DR5 > PRY5 > 5 > C6 > 6 > S5-C8
        > S5-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 82.0121088194467
    # Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
    'series_5_blueprint_only_cube': """
        S5-DR0.5 > S5-PRY0.5 > S5-H0.5 > S5-H1 > S5-H2 > S5-DR2.5 > S5-DR5
        > 0.5 > S5-DR8 > reset > S5-H4 > S5-Q1 > Q1 > H1 > 1 > S5-G1.5 > G1.5
        > 1.5 > S5-G2.5 > S5-Q2 > S5-E-315 > S5-E-031 > Q2 > E2 > H2 > 2
        > S5-PRY2.5 > S5-G4 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S5-Q4 > Q4 > G4
        > H4 > 4 > S5-PRY5 > S5-PRY8 > S5-C6 > DR5 > PRY5 > 5 > C6 > 6
        > S5-C8 > S5-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 124.71616166666873
    # Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
    'series_5_blueprint_only': """
        S5-DR0.5 > S5-H0.5 > S5-PRY0.5 > S5-DR8 > S5-DR5 > S5-DR2.5
        > S5-G1.5 > S5-PRY2.5 > 0.5 > S5-G2.5 > S5-G4 > reset > S5-Q1 > Q1
        > 1 > S5-PRY5 > G1.5 > 1.5 > S5-Q2 > S5-E-031 > S5-E-315 > Q2 > E2
        > 2 > S5-PRY8 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S5-Q4 > Q4 > G4 > 4
        > S5-C6 > DR5 > PRY5 > 5 > C6 > 6 > S5-C8 > DR8 > PRY8 > C8 > 8
        > S5-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 153.41706666666678
    # Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
    'series_4_tenrai_only_cube': """
        S4-Q0.5 > S4-DR0.5 > S4-PRY0.5 > Q0.5 > S4-Q4 > S4-Q2 > S4-Q1 > 0.5
        > S4-E-315 > S4-G1.5 > S4-G4 > Q1 > reset > S4-H1 > H1 > 1 > S4-E-031
        > S4-DR2.5 > S4-PRY2.5 > S4-G2.5 > G1.5 > 1.5 > Q2 > E2 > S4-H2 > H2
        > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S4-DR5 > S4-PRY5 > Q4 > G4
        > S4-H4 > H4 > 4 > S4-C6 > DR5 > PRY5 > 5 > S4-DR8 > S4-PRY8 > S4-C8
        > C6 > 6 > S4-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 161.37177965277806
    # Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
    'series_4_tenrai_only': """
        S4-Q0.5 > S4-PRY0.5 > S4-DR0.5 > Q0.5 > S4-Q4 > S4-Q2 > S4-Q1 > 0.5
        > S4-E-315 > S4-G4 > S4-G1.5 > Q1 > 1 > S4-E-031 > S4-DR2.5 > reset
        > S4-G2.5 > S4-PRY2.5 > G1.5 > 1.5 > Q2 > E2 > 2 > DR2.5 > PRY2.5
        > G2.5 > 2.5 > S4-DR5 > S4-PRY5 > Q4 > G4 > 4 > S4-C6 > DR5 > PRY5
        > 5 > S4-DR8 > S4-PRY8 > S4-C8 > C6 > 6 > DR8 > PRY8 > C8 > 8
        > S4-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 124.67622465277958
    # Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
    'series_4_blueprint_tenrai_cube': """
        S4-DR0.5 > S4-Q0.5 > S4-PRY0.5 > 0.5 > S4-DR2.5 > S4-Q1 > S4-Q2
        > S4-H1 > S4-E-315 > S4-G1.5 > reset > S4-Q4 > S4-G4 > S4-H2 > Q1
        > H1 > 1 > S4-G2.5 > S4-DR5 > S4-PRY2.5 > G1.5 > 1.5 > S4-E-031
        > S4-DR8 > Q2 > E2 > H2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S4-H4
        > S4-PRY5 > Q4 > G4 > H4 > 4 > S4-C6 > S4-PRY8 > DR5 > PRY5 > 5 > C6
        > 6 > S4-C8 > DR8 > PRY8 > C8 > 8 > S4-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 143.56399131945145
    # Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
    'series_4_blueprint_tenrai': """
        S4-DR0.5 > S4-PRY0.5 > S4-Q0.5 > S4-H0.5 > Q0.5 > S4-DR2.5
        > S4-G1.5 > S4-Q1 > S4-DR5 > 0.5 > S4-G4 > S4-Q2 > S4-PRY2.5 > reset
        > S4-DR8 > Q1 > 1 > S4-E-315 > S4-G2.5 > G1.5 > 1.5 > S4-E-031
        > S4-Q4 > Q2 > E2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S4-PRY5
        > S4-PRY8 > Q4 > G4 > 4 > S4-C6 > DR5 > PRY5 > 5 > C6 > 6 > S4-C8
        > S4-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 82.0121088194467
    # Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
    'series_4_blueprint_only_cube': """
        S4-DR0.5 > S4-PRY0.5 > S4-H0.5 > S4-H1 > S4-H2 > S4-DR2.5 > S4-DR5
        > 0.5 > S4-DR8 > reset > S4-H4 > S4-Q1 > Q1 > H1 > 1 > S4-G1.5 > G1.5
        > 1.5 > S4-G2.5 > S4-Q2 > S4-E-315 > S4-E-031 > Q2 > E2 > H2 > 2
        > S4-PRY2.5 > S4-G4 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S4-Q4 > Q4 > G4
        > H4 > 4 > S4-PRY5 > S4-PRY8 > S4-C6 > DR5 > PRY5 > 5 > C6 > 6
        > S4-C8 > S4-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 124.71616166666873
    # Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
    'series_4_blueprint_only': """
        S4-DR0.5 > S4-H0.5 > S4-PRY0.5 > S4-DR8 > S4-DR5 > S4-DR2.5
        > S4-G1.5 > S4-PRY2.5 > 0.5 > S4-G2.5 > S4-G4 > reset > S4-Q1 > Q1
        > 1 > S4-PRY5 > G1.5 > 1.5 > S4-Q2 > S4-E-031 > S4-E-315 > Q2 > E2
        > 2 > S4-PRY8 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S4-Q4 > Q4 > G4 > 4
        > S4-C6 > DR5 > PRY5 > 5 > C6 > 6 > S4-C8 > DR8 > PRY8 > C8 > 8
        > S4-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 153.41706666666678
    # Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
    'series_3_234_only_cube': """
        S3-Q0.5 > S3-DR0.5 > S3-PRY0.5 > Q0.5 > S3-Q4 > S3-Q2 > S3-Q1 > 0.5
        > S3-E-315 > S3-G1.5 > S3-G4 > Q1 > reset > S3-H1 > H1 > 1 > S3-E-031
        > S3-DR2.5 > S3-PRY2.5 > S3-G2.5 > G1.5 > 1.5 > Q2 > E2 > S3-H2 > H2
        > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S3-DR5 > S3-PRY5 > Q4 > G4
        > S3-H4 > H4 > 4 > S3-C6 > DR5 > PRY5 > 5 > S3-DR8 > S3-PRY8 > S3-C8
        > C6 > 6 > S3-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 161.37177965277806
    # Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
    'series_3_234_only': """
        S3-Q0.5 > S3-PRY0.5 > S3-DR0.5 > Q0.5 > S3-Q4 > S3-Q2 > S3-Q1 > 0.5
        > S3-E-315 > S3-G4 > S3-G1.5 > Q1 > 1 > S3-E-031 > S3-DR2.5 > reset
        > S3-G2.5 > S3-PRY2.5 > G1.5 > 1.5 > Q2 > E2 > 2 > DR2.5 > PRY2.5
        > G2.5 > 2.5 > S3-DR5 > S3-PRY5 > Q4 > G4 > 4 > S3-C6 > DR5 > PRY5
        > 5 > S3-DR8 > S3-PRY8 > S3-C8 > C6 > 6 > DR8 > PRY8 > C8 > 8
        > S3-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 124.67622465277958
    # Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
    'series_3_blueprint_234_cube': """
        S3-DR0.5 > S3-Q0.5 > S3-PRY0.5 > 0.5 > S3-DR2.5 > S3-Q1 > S3-Q2
        > S3-H1 > S3-E-315 > S3-G1.5 > reset > S3-Q4 > S3-G4 > S3-H2 > Q1
        > H1 > 1 > S3-G2.5 > S3-DR5 > S3-PRY2.5 > G1.5 > 1.5 > S3-E-031
        > S3-DR8 > Q2 > E2 > H2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S3-H4
        > S3-PRY5 > Q4 > G4 > H4 > 4 > S3-C6 > S3-PRY8 > DR5 > PRY5 > 5 > C6
        > 6 > S3-C8 > DR8 > PRY8 > C8 > 8 > S3-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 143.56399131945145
    # Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
    'series_3_blueprint_234': """
        S3-DR0.5 > S3-PRY0.5 > S3-Q0.5 > S3-H0.5 > Q0.5 > S3-DR2.5
        > S3-G1.5 > S3-Q1 > S3-DR5 > 0.5 > S3-G4 > S3-Q2 > S3-PRY2.5 > reset
        > S3-DR8 > Q1 > 1 > S3-E-315 > S3-G2.5 > G1.5 > 1.5 > S3-E-031
        > S3-Q4 > Q2 > E2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S3-PRY5
        > S3-PRY8 > Q4 > G4 > 4 > S3-C6 > DR5 > PRY5 > 5 > C6 > 6 > S3-C8
        > S3-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 82.0121088194467
    # Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
    'series_3_blueprint_only_cube': """
        S3-DR0.5 > S3-PRY0.5 > S3-H0.5 > S3-H1 > S3-H2 > S3-DR2.5 > S3-DR5
        > 0.5 > S3-DR8 > reset > S3-H4 > S3-Q1 > Q1 > H1 > 1 > S3-G1.5 > G1.5
        > 1.5 > S3-G2.5 > S3-Q2 > S3-E-315 > S3-E-031 > Q2 > E2 > H2 > 2
        > S3-PRY2.5 > S3-G4 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S3-Q4 > Q4 > G4
        > H4 > 4 > S3-PRY5 > S3-PRY8 > S3-C6 > DR5 > PRY5 > 5 > C6 > 6
        > S3-C8 > S3-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 124.71616166666873
    # Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
    'series_3_blueprint_only': """
        S3-DR0.5 > S3-H0.5 > S3-PRY0.5 > S3-DR8 > S3-DR5 > S3-DR2.5
        > S3-G1.5 > S3-PRY2.5 > 0.5 > S3-G2.5 > S3-G4 > reset > S3-Q1 > Q1
        > 1 > S3-PRY5 > G1.5 > 1.5 > S3-Q2 > S3-E-031 > S3-E-315 > Q2 > E2
        > 2 > S3-PRY8 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S3-Q4 > Q4 > G4 > 4
        > S3-C6 > DR5 > PRY5 > 5 > C6 > 6 > S3-C8 > DR8 > PRY8 > C8 > 8
        > S3-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 153.41706666666678
    # Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
    'series_2_457_only_cube': """
        S2-Q0.5 > S2-DR0.5 > S2-PRY0.5 > Q0.5 > S2-Q4 > S2-Q2 > S2-Q1 > 0.5
        > S2-E-315 > S2-G1.5 > S2-G4 > Q1 > reset > S2-H1 > H1 > 1 > S2-E-031
        > S2-DR2.5 > S2-PRY2.5 > S2-G2.5 > G1.5 > 1.5 > Q2 > E2 > S2-H2 > H2
        > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S2-DR5 > S2-PRY5 > Q4 > G4
        > S2-H4 > H4 > 4 > S2-C6 > DR5 > PRY5 > 5 > S2-DR8 > S2-PRY8 > S2-C8
        > C6 > 6 > S2-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
    # Average time cost: 161.37177965277806
    # Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
    'series_2_457_only': """
        S2-Q0.5 > S2-PRY0.5 > S2-DR0.5 > Q0.5 > S2-Q4 > S2-Q2 > S2-Q1 > 0.5
        > S2-E-315 > S2-G4 > S2-G1.5 > Q1 > 1 > S2-E-031 > S2-DR2.5 > reset
        > S2-G2.5 > S2-PRY2.5 > G1.5 > 1.5 > Q2 > E2 > 2 > DR2.5 > PRY2.5
        > G2.5 > 2.5 > S2-DR5 > S2-PRY5 > Q4 > G4 > 4 > S2-C6 > DR5 > PRY5
        > 5 > S2-DR8 > S2-PRY8 > S2-C8 > C6 > 6 > DR8 > PRY8 > C8 > 8
        > S2-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 124.67622465277958
    # Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
    'series_2_blueprint_457_cube': """
        S2-DR0.5 > S2-Q0.5 > S2-PRY0.5 > 0.5 > S2-DR2.5 > S2-Q1 > S2-Q2
        > S2-H1 > S2-E-315 > S2-G1.5 > reset > S2-Q4 > S2-G4 > S2-H2 > Q1
        > H1 > 1 > S2-G2.5 > S2-DR5 > S2-PRY2.5 > G1.5 > 1.5 > S2-E-031
        > S2-DR8 > Q2 > E2 > H2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S2-H4
        > S2-PRY5 > Q4 > G4 > H4 > 4 > S2-C6 > S2-PRY8 > DR5 > PRY5 > 5 > C6
        > 6 > S2-C8 > DR8 > PRY8 > C8 > 8 > S2-C12 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
    # Average time cost: 143.56399131945145
    # Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
    'series_2_blueprint_457': """
        S2-DR0.5 > S2-PRY0.5 > S2-Q0.5 > S2-H0.5 > Q0.5 > S2-DR2.5
        > S2-G1.5 > S2-Q1 > S2-DR5 > 0.5 > S2-G4 > S2-Q2 > S2-PRY2.5 > reset
        > S2-DR8 > Q1 > 1 > S2-E-315 > S2-G2.5 > G1.5 > 1.5 > S2-E-031
        > S2-Q4 > Q2 > E2 > 2 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S2-PRY5
        > S2-PRY8 > Q4 > G4 > 4 > S2-C6 > DR5 > PRY5 > 5 > C6 > 6 > S2-C8
        > S2-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 82.0121088194467
    # Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
    'series_2_blueprint_only_cube': """
        S2-DR0.5 > S2-PRY0.5 > S2-H0.5 > S2-H1 > S2-H2 > S2-DR2.5 > S2-DR5
        > 0.5 > S2-DR8 > reset > S2-H4 > S2-Q1 > Q1 > H1 > 1 > S2-G1.5 > G1.5
        > 1.5 > S2-G2.5 > S2-Q2 > S2-E-315 > S2-E-031 > Q2 > E2 > H2 > 2
        > S2-PRY2.5 > S2-G4 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S2-Q4 > Q4 > G4
        > H4 > 4 > S2-PRY5 > S2-PRY8 > S2-C6 > DR5 > PRY5 > 5 > C6 > 6
        > S2-C8 > S2-C12 > DR8 > PRY8 > C8 > 8 > C12 > 12
    """,
    # Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
    # Average time cost: 124.71616166666873
    # Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
    'series_2_blueprint_only': """
        S2-DR0.5 > S2-H0.5 > S2-PRY0.5 > S2-DR8 > S2-DR5 > S2-DR2.5
        > S2-G1.5 > S2-PRY2.5 > 0.5 > S2-G2.5 > S2-G4 > reset > S2-Q1 > Q1
        > 1 > S2-PRY5 > G1.5 > 1.5 > S2-Q2 > S2-E-031 > S2-E-315 > Q2 > E2
        > 2 > S2-PRY8 > DR2.5 > PRY2.5 > G2.5 > 2.5 > S2-Q4 > Q4 > G4 > 4
        > S2-C6 > DR5 > PRY5 > 5 > C6 > 6 > S2-C8 > DR8 > PRY8 > C8 > 8
        > S2-C12 > C12 > 12
    """,
    # Old community filters
    'series_2_than_3_457_234': """
        S2-Q0.5 > S2-PRY0.5 > S2-DR0.5 > S2-Q4 > S2-Q1 > S2-Q2 > S2-H0.5
        > 0.5 > S3-Q1 > S3-Q2 > S2-G4 > S3-Q4 > S2-G1.5 > S2-DR2.5 > reset
        > Q1 > S2-PRY2.5 > S2-G2.5 > H1 > 1.5 > Q2 > 2.5 > S2-DR5 > S2-PRY5
        > Q4 > G4 > 5 > H2 > S2-C6 > S2-DR8 > S2-PRY8 > S2-C8 > 6 > 8 > 4
        > S2-C12 > 12
    """,
}
