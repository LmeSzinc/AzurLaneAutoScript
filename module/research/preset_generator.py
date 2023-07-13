import re


def split_filter(string):
    if isinstance(string, list):
        return string
    return [f.strip(' \t\r\n') for f in string.split('>')]


def join_filter(selection):
    if isinstance(selection, str):
        return selection
    return ' > '.join(selection)


def beautify_filter(list_filter):
    if isinstance(list_filter, str):
        list_filter = split_filter(list_filter)

    out = []
    length = 0
    for selection in list_filter:
        if length + len(selection) + 3 > 70:
            out.append('\n')
            length = 0
        out.append(selection)
        length += len(selection) + 3
    string = ' > '.join(out).strip('\n >').replace(' > \n', '\n').replace('\n ', '\n')
    return string


def translate(string: str, target='series_4_tenrai_only_cube', for_simulate=False):
    res = re.search(r'series_?(\d)', target)
    if res:
        series = res.group(1)
    else:
        print(f'Translate target from unknown series: {target}')
        return
    cube = 'cube' in target
    string = string.replace('S4-H0.5 > !4-0.5', '0.5')
    string = string.replace('!4-0.5', '0.5')
    # Add Q0.5 after the last 0.5 selection
    selections = split_filter(string)
    last_05 = 0
    for index, sele in enumerate(selections):
        if sele == '0.5':
            break
        if '0.5' in sele:
            last_05 = index
    if last_05:
        selections.insert(last_05 + 1, 'Q0.5')
    string = join_filter(selections)
    string = string.replace('S4-Q0.5 > Q0.5 > 0.5', '0.5')
    string = string.replace('Q0.5 > 0.5', '0.5')

    string = string.replace('!4-1.5', 'G1.5 > 1.5')
    string = string.replace('!4-1', 'Q1 > H1 > 1')
    string = string.replace('!4-2.5', 'DR2.5 > PRY2.5 > G2.5 > 2.5')
    string = string.replace('!4-2', 'Q2 > E2 > H2 > 2')
    string = string.replace('!4-4', 'Q4 > G4 > H4 > 4')
    string = string.replace('!4-5', 'DR5 > PRY5 > 5')
    string = string.replace('!4-C6', 'C6 > 6')
    string = string.replace('!4-C8', 'DR8 > PRY8 > C8 > 8')
    string = string.replace('!4-C12', 'C12 > 12')

    if not for_simulate:
        string = string.replace('A2', 'E-315')
        string = string.replace('Z2', 'E-031')

    if not cube:
        string = re.sub(r'(S4-)?H[124] > ', '', string)
    string = string.replace('H1 > 1 > reset > S4-H1', 'reset > S4-H1 > H1 > 1')
    string = string.replace('H1 > 1 > S4-H1', 'S4-H1 > H1 > 1')
    string = string.replace('H2 > 2 > S4-H2', 'S4-H2 > H2 > 2')
    string = string.replace('H4 > 4 > S4-H4', 'S4-H4 > H4 > 4')
    string = re.sub(r'S4', f'S{series}', string)

    return beautify_filter(string)


def convert_name(name, series):
    name = re.sub(r'series_\d', f'series_{series}', name)
    if 'series_6' in name:
        name = name.replace('tenrai', '203')
    if 'series_5' in name:
        name = name.replace('tenrai', '152')
    if 'series_4' in name:
        pass
    if 'series_3' in name:
        name = name.replace('tenrai', '234')
    if 'series_2' in name:
        name = name.replace('tenrai', '457')
    return name


if __name__ == '__main__':
    from module.config.code_generator import *

    Value(FILTER_STRING_SHORTEST='0.5 > 1 > 1.5 > 2 > 2.5 > 3 > 4 > 5 > 6 > 8 > 10 > 12')
    Value(
        FILTER_STRING_CHEAPEST='Q1 > Q2 > T3 > T4 > Q4 > C6 > T6 > C8 > C12 > G1.5 > D2.5 > G2.5 > D5 > Q0.5 > G4 > D8 > H1 > H2 > H0.5 > D0.5 > H4')
    with Dict('DICT_FILTER_PRESET'):
        for series in [6, 5, 4, 3, 2]:
            def new_filter(**kwargs):
                for k, v in kwargs.items():
                    k = convert_name(k, series)
                    v = translate(v, target=k)
                    DictItem(k, v)

            # 1
            Comment("""
                Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
                Average time cost: 153.41706666666678
                Average rewards: [238.69016631 238.37881965 529.71190834 528.92520834 528.39586667 150.07973333]
            """)
            new_filter(series_4_tenrai_only_cube="""
                S4-Q0.5 > S4-DR0.5 > S4-PRY0.5 > S4-Q4 > S4-Q2 > S4-Q1 > !4-0.5
                > S4-A2 > S4-G1.5 > S4-G4 > !4-1 > reset > S4-H1 > S4-Z2 
                > S4-DR2.5 > S4-PRY2.5 > S4-G2.5 > !4-1.5 > !4-2 > S4-H2 > !4-2.5 > S4-DR5 > S4-PRY5 
                > !4-4 > S4-H4 > S4-C6 > !4-5 > S4-DR8 > S4-PRY8 > S4-C8 > !4-C6 > S4-C12
                > !4-C8 > !4-C12
            """)
            # 2
            Comment("""
                Goal: DR_blurprint=0, PRY_blueprint=0, tanrai_blueprint=150
                Average time cost: 161.37177965277806
                Average rewards: [241.92774575 241.13046242 421.82134358 421.04494941 420.46893024 150.07799978]
            """)
            new_filter(series_4_tenrai_only="""
                S4-Q0.5 > S4-PRY0.5 > S4-DR0.5 > S4-Q4 > S4-Q2 > S4-Q1 > S4-H0.5 > !4-0.5 > S4-A2
                > S4-G4 > S4-H1 > S4-G1.5 > !4-1 > S4-Z2 > S4-DR2.5 > reset
                > S4-G2.5 > S4-PRY2.5 > !4-1.5 > !4-2 > !4-2.5 > S4-H2 > S4-H4 > S4-DR5
                > S4-PRY5 > !4-4 > S4-C6 > !4-5 > S4-DR8 > S4-PRY8 > S4-C8 > !4-C6
                > !4-C8 > S4-C12 > !4-C12
            """)
            # 5
            Comment("""
                Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
                Average time cost: 124.67622465277958
                Average rewards: [531.93022864 529.81919864 510.27473326 510.18530159 510.11215826 100.8088164]
            """)
            new_filter(series_4_blueprint_tenrai_cube="""
                S4-DR0.5 > S4-Q0.5 > S4-PRY0.5 > S4-H0.5 > !4-0.5 > S4-DR2.5 > S4-Q1
                > S4-Q2 > S4-H1 > S4-A2 > S4-G1.5 > reset > S4-Q4 > S4-G4 > S4-H2
                > !4-1 > S4-G2.5 > S4-DR5 > S4-PRY2.5 > !4-1.5 > S4-Z2 > S4-DR8
                > !4-2 > !4-2.5 > S4-H4 > S4-PRY5 > !4-4 > S4-C6 > S4-PRY8 > !4-5 > !4-C6 > S4-C8
                > !4-C8 > S4-C12 > !4-C12
            """)
            # 6
            Comment("""
                Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=100
                Average time cost: 143.56399131945145
                Average rewards: [520.06195858 519.19883191 392.86544828 392.64870495 392.49383995 102.2368499]
            """)
            new_filter(series_4_blueprint_tenrai="""
                S4-DR0.5 > S4-PRY0.5 > S4-Q0.5 > S4-H1 > S4-H0.5 > S4-DR2.5 > S4-G1.5
                > S4-Q1 > S4-DR5 > !4-0.5 > S4-G4 > S4-Q2 > S4-PRY2.5 > reset > S4-DR8
                > !4-1 > S4-A2 > S4-G2.5 > S4-H2 > !4-1.5 > S4-Z2 > S4-H4
                > S4-Q4 > !4-2  > !4-2.5 > S4-PRY5 > S4-PRY8 > !4-4 > S4-C6 > !4-5 > !4-C6 > S4-C8
                > S4-C12 > !4-C8 > !4-C12
            """)
            # 3
            Comment("""
                Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
                Average time cost: 82.0121088194467
                Average rewards: [519.0311752  514.64003687 653.77171198 653.72126532 653.66129615 26.97694791]
            """)
            new_filter(series_4_blueprint_only_cube="""
                S4-DR0.5 > S4-PRY0.5 > S4-H0.5 > S4-H1 > S4-H2 > S4-DR2.5 > S4-DR5 > S4-Q0.5
                > !4-0.5 > S4-DR8 > reset > S4-H4 > S4-Q1 > !4-1 > S4-G1.5 > !4-1.5
                > S4-G2.5 > S4-Q2 > S4-A2 > S4-Z2 > !4-2 > S4-PRY2.5 > S4-G4 > !4-2.5
                > S4-Q4 > !4-4 > S4-PRY5 > S4-PRY8 > S4-C6 > !4-5 > !4-C6 > S4-C8
                > S4-C12 > !4-C8 > !4-C12
            """)
            # 4
            Comment("""
                Goal: DR_blurprint=513, PRY_blueprint=343, tanrai_blueprint=0
                Average time cost: 124.71616166666873
                Average rewards: [514.96354877 514.70099977 355.58865468 354.96831385 354.66888635 56.48432238]
            """)
            new_filter(series_4_blueprint_only="""
                S4-DR0.5 > S4-H0.5 > S4-PRY0.5 > S4-DR8 > S4-DR5
                > S4-DR2.5 > S4-G1.5 > S4-PRY2.5 > S4-Q0.5 > !4-0.5 > S4-G2.5 > S4-G4
                > reset > S4-Q1 > !4-1 > S4-PRY5 > !4-1.5 > S4-Q2 > S4-Z2 > S4-A2 > !4-2 > S4-PRY8
                > !4-2.5 > S4-Q4 > !4-4 > S4-C6 > !4-5 > !4-C6 > S4-C8
                > !4-C8 > S4-C12 > !4-C12
            """)

        Comment('Old community filters')
        DictItem('series_2_than_3_457_234', beautify_filter("""
            S2-Q0.5 > S2-PRY0.5 > S2-DR0.5 > S2-Q4 > S2-Q1 > S2-Q2 > S2-H0.5 > 0.5
            > S3-Q1 > S3-Q2 > S2-G4 > S3-Q4 > S2-G1.5 > S2-DR2.5 > reset > Q1 > S2-PRY2.5 > S2-G2.5 > H1 > 1.5
            > Q2 > 2.5 > S2-DR5 > S2-PRY5 > Q4 > G4 > 5 > H2 > S2-C6 > S2-DR8 > S2-PRY8 > S2-C8
            > 6 > 8 > 4 > S2-C12 > 12
        """))
    from module.logger import logger
    generator.write('./module/research/preset.py')
