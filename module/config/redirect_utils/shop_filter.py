import re

FILTER_REGEX = re.compile(
    "(pr|dr)"
    "([1-4]"
    "|neptune|monarch|ibuki|izumo|roon|saintlouis"
    "|seattle|georgia|kitakaze|azuma|friedrich"
    "|gascogne|champagne|cheshire|drake|mainz|odin"
    "|anchorage|hakuryu|agir|august|marcopolo)?"
    "(bp)",
    flags=re.IGNORECASE,
)

NAME_TO_SERIES = {
    "neptune": 1,
    "monarch": 1,
    "ibuki": 1,
    "izumo": 1,
    "roon": 1,
    "saintlouis": 1,
    "seattle": 2,
    "georgia": 2,
    "kitakaze": 2,
    "gascogne": 2,
    "azuma": 2,
    "friedrich": 2,
    "cheshire": 3,
    "mainz": 3,
    "odin": 3,
    "champagne": 3,
    "drake": 3,
    "anchorage": 4,
    "august": 4,
    "marcopolo": 4,
    "agir": 4,
    "hakuryu": 4,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}


def bp_redirect(value):
    """
    Redirects shop filter old format for research blueprints
    to new format
    PRBP = PR; PR1BP = PRS1; PROdinBP = PROdin/PROdinS3
    likewise for DR variants
    """
    matches = re.findall(FILTER_REGEX, value)
    if not matches:
        return value

    for match in matches:
        flat = "".join(match)
        if match[1]:
            if match[1].isnumeric():
                value = re.sub(
                    flat, f"{match[0]}S{NAME_TO_SERIES[match[1].lower()]}", value
                )
            else:
                value = re.sub(
                    flat,
                    f"{match[0]}{match[1]}S{NAME_TO_SERIES[match[1].lower()]}",
                    value,
                )
        else:
            value = re.sub(flat, match[0], value)

    return value


if __name__ == "__main__":
    print(
        bp_redirect(
            "PlateGeneralT1 > DRAgirBP > CatT3 > PROdinBP > Chip > PR1BP > PRBP > DRDrakeBP > DR2BP"
        )
    )
