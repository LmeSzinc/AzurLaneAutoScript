import re

FILTER_REGEX_SERIES = re.compile(
    '(pr|dr)'

    '([1-4]'
    '|neptune|monarch|ibuki|izumo|roon|saintlouis'
    '|seattle|georgia|kitakaze|azuma|friedrich'
    '|gascogne|champagne|cheshire|drake|mainz|odin'
    '|anchorage|hakuryu|agir|august|marcopolo)?'

    '(bp)',
    flags=re.IGNORECASE)

NAME_TO_SERIES = {
    'neptune': 1, 'monarch': 1, 'ibuki': 1, 'izumo': 1, 'roon': 1, 'saintlouis': 1,
    'seattle': 2, 'georgia': 2, 'kitakaze': 2, 'gascogne': 2, 'azuma': 2, 'friedrich': 2,
    'cheshire': 3, 'mainz': 3, 'odin': 3, 'champagne': 3, 'drake': 3,
    'anchorage': 4, 'august': 4, 'marcopolo': 4, 'agir': 4, 'hakuryu': 4,
    '1': 1, '2': 2, '3': 3, '4': 4,
}


def bp_redirect(value):
    """
    Redirects shop filter old format for research blueprints
    to new format
    PRBP = PR; PR1BP = PRS1; PROdinBP = PROdin/PROdinS3
    likewise for DR variants
    """
    matches = re.findall(FILTER_REGEX_SERIES, value)
    if not matches:
        return value

    for match in matches:
        flat = ''.join(match)
        if match[1]:
            if match[1].isnumeric():
                value = re.sub(flat, f'{match[0]}S{NAME_TO_SERIES[match[1].lower()]}', value)
            else:
                value = re.sub(flat, f'{match[0]}{match[1]}S{NAME_TO_SERIES[match[1].lower()]}', value)
        else:
            value = re.sub(flat, match[0], value)

    return value


FILTER_REGEX_VOUCHER = re.compile(
    '(logger)'

    '(archive|unlock)?'

    '(t[1-6])?',
    flags=re.IGNORECASE)


def voucher_redirect(value):
    """
    Redirects voucher shop filter to prevents users
    from using banned strings i.e. Logger, LoggerT[1-6],
    LoggerArchive, or LoggerArchiveT[1-6]
    Banned strings are used for special circumstances
    handled by ALAS
    """
    matches = re.findall(FILTER_REGEX_VOUCHER, value)
    if not matches:
        return value

    for match in matches:
        flat = ''.join(match)
        pattern = rf'\b{flat}\b'
        if (match[2] and match[1]) or match[1]:
            value = re.sub(pattern, '', value)
            value = re.sub('\>\s*\>', '>', value)
            value = re.sub('\>\s*$', '', value)
        elif match[2]:
            value = re.sub(pattern, f'LoggerAbyssal{match[2].upper()} > LoggerObscure{match[2].upper()}', value)
        else:
            value = re.sub(pattern, f'LoggerAbyssal > LoggerObscure', value)

    return value

if __name__ == '__main__':
    print(bp_redirect('PlateGeneralT1 > DRAgirBP > CatT3 > PROdinBP > Chip > PR1BP > PRBP > DRDrakeBP > DR2BP'))
    print(voucher_redirect('Coin > HECombatPlan > LoggerArchive > TuningCombatT2 > LoggerArchiveT1 > LoggerT6 > Logger > LoggerUnlockT2'))
