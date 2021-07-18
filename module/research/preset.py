FILTER_STRING_SHORTEST = '0.5 > 1 > 1.5 > 2 > 2.5 > 3 > 4 > 5 > 6 > 8 > 10 > 12'
FILTER_STRING_CHEAPEST = 'Q1 > Q2 > T3 > T4 > Q4 > C6 > T6 > C8 > C12 > G1.5 > D2.5 > G2.5 > D5 > Q0.5 > G4 > D8 > H1 > H2 > H0.5 > D0.5 > H4'
DICT_FILTER_PRESET = {
    'series_4': 'S4-DR0.5 > S4-PRY0.5 > S4-Q0.5 > Q0.5 > S4-H1 > S4-DR2.5 > S4-DR8 > S4-DR5 > S4-H2 > S4-H4 > S4-Q1 > S4-Q2 > S4-Q4 > S4-G4 > S4-G1.5 > S4-G2 > S4-PRY2.5 > S4-PRY5 > S4-PRY8 > reset > shortest',
    'series_3': 'S3-DR-0.5 > S3-0.5 > Q0.5 > S3-DR-2.5 > S3-DR-8 > S3-DR-5 > S3-H-1 > S3-H-4 > S3-H-2 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > shortest',
    'series_3_than_2': 'S3-DR-0.5 > S3-0.5 > S2-DR-0.5 > Q0.5 > S3-DR-2.5 > S3-DR-8 > S3-DR-5 > S3-H-1 > S3-H-4 > S3-H-2 > S2-DR-2.5 > S2-DR-8 > S2-DR-5 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > shortest',
    'series_3_fastest': 'S3-DR-0.5 > S3-0.5 > S3-DR-2.5 > S3-H-1 > S3-H-4 > S3-H-2 > S3-DR-8 > S3-DR-5 > Q1 > Q2 > reset > shortest',
    'free_research_only': 'C12 > C8 > C6 > Q1 > Q2 > Q4 > T3 > T4 > T6 > reset > cheapest',
    'cubes_to_chips': 'Q0.5 > H0.5 > H1 > H2 > H4 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > cheapest',
}
