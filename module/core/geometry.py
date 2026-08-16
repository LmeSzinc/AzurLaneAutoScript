import re

REGEX_NODE = re.compile(r"(-?[A-Za-z]+)(-?\d+)")


def ensure_int(*args):
    """
    Convert all elements to int.
    Return the same structure as nested objects.

    Args:
        *args:

    Returns:
        list:
    """

    def to_int(item):
        try:
            return int(item)
        except TypeError:
            result = [to_int(i) for i in item]
            if len(result) == 1:
                result = result[0]
            return result

    return to_int(args)


def area_offset(area, offset):
    """
    Move an area.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        offset: (x, y).

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    upper_left_x, upper_left_y, bottom_right_x, bottom_right_y = area
    x, y = offset
    return upper_left_x + x, upper_left_y + y, bottom_right_x + x, bottom_right_y + y


def area_pad(area, pad=10):
    """
    Inner offset an area.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        pad (int):

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    upper_left_x, upper_left_y, bottom_right_x, bottom_right_y = area
    return upper_left_x + pad, upper_left_y + pad, bottom_right_x - pad, bottom_right_y - pad


def limit_in(x, lower, upper):
    """
    Limit x within range (lower, upper)

    Args:
        x:
        lower:
        upper:

    Returns:
        int, float:
    """
    return max(min(x, upper), lower)


def area_limit(area1, area2):
    """
    Limit an area in another area.

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    x_lower, y_lower, x_upper, y_upper = area2
    return (
        limit_in(area1[0], x_lower, x_upper),
        limit_in(area1[1], y_lower, y_upper),
        limit_in(area1[2], x_lower, x_upper),
        limit_in(area1[3], y_lower, y_upper),
    )


def area_size(area):
    """
    Area size or shape.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (x, y).
    """
    return (max(area[2] - area[0], 0), max(area[3] - area[1], 0))


def point_limit(point, area):
    """
    Limit point in an area.

    Args:
        point: (x, y).
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (x, y).
    """
    return (limit_in(point[0], area[0], area[2]), limit_in(point[1], area[1], area[3]))


def point_in_area(point, area, threshold=5):
    """

    Args:
        point: (x, y).
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    return area[0] - threshold < point[0] < area[2] + threshold and area[1] - threshold < point[1] < area[3] + threshold


def area_in_area(area1, area2, threshold=5):
    """

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    return (
        area2[0] - threshold <= area1[0]
        and area2[1] - threshold <= area1[1]
        and area1[2] <= area2[2] + threshold
        and area1[3] <= area2[3] + threshold
    )


def area_cross_area(area1, area2, threshold=5):
    """

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    # https://www.yiiven.cn/rect-is-intersection.html
    xa1, ya1, xa2, ya2 = area1
    xb1, yb1, xb2, yb2 = area2
    return (
        abs(xb2 + xb1 - xa2 - xa1) <= xa2 - xa1 + xb2 - xb1 + threshold * 2
        and abs(yb2 + yb1 - ya2 - ya1) <= ya2 - ya1 + yb2 - yb1 + threshold * 2
    )


def float2str(n, decimal=3):
    """
    Args:
        n (float):
        decimal (int):

    Returns:
        str:
    """
    return str(round(n, decimal)).ljust(decimal + 2, "0")


def point2str(x, y, length=4):
    """
    Args:
        x (int, float):
        y (int, float):
        length (int): Align length.

    Returns:
        str: String with numbers right aligned, such as '( 100,  80)'.
    """
    return "(%s, %s)" % (str(int(x)).rjust(length), str(int(y)).rjust(length))


def col2name(col):
    """
    Convert a zero indexed column cell reference to a string.

    Args:
       col: The cell column. Int.

    Returns:
        Column style string.

    Examples:
        0 -> A, 3 -> D, 35 -> AJ, -1 -> -A
    """

    col_neg = col < 0
    if col_neg:
        col_num = -col
    else:
        col_num = col + 1  # Change to 1-index.
    col_str = ""

    while col_num:
        # Set remainder from 1 .. 26
        remainder = col_num % 26

        if remainder == 0:
            remainder = 26

        # Convert the remainder to a character.
        col_letter = chr(remainder + 64)

        # Accumulate the column letters, right to left.
        col_str = col_letter + col_str

        # Get the next order of magnitude.
        col_num = int((col_num - 1) / 26)

    if col_neg:
        return "-" + col_str
    else:
        return col_str


def name2col(col_str):
    """
    Convert a cell reference in A1 notation to a zero indexed row and column.

    Args:
       col_str:  A1 style string.

    Returns:
        row, col: Zero indexed cell row and column indices.
    """
    # Convert base26 column string to number.
    col = 0
    col_neg = col_str.startswith("-")
    col_str = col_str.strip("-").upper()

    for expn, char in enumerate(reversed(col_str)):
        col += (ord(char) - 64) * (26**expn)

    if col_neg:
        return -col
    else:
        return col - 1


def node2location(node):
    """
    See location2node()

    Args:
        node (str): Example: 'E3'

    Returns:
        tuple[int]: Example: (4, 2)
    """
    res = REGEX_NODE.search(node)
    if res:
        x, y = res.group(1), res.group(2)
        y = int(y)
        if y > 0:
            y -= 1
        return name2col(x), y
    else:
        # Whatever
        return ord(node[0]) % 32 - 1, int(node[1:]) - 1


def location2node(location):
    """
    Convert location tuple to an Excel-like cell.
    Accept negative values also.

         -2   -1    0    1    2    3
    -2 -B-2 -A-2  A-2  B-2  C-2  D-2
    -1 -B-1 -A-1  A-1  B-1  C-1  D-1
     0  -B1  -A1   A1   B1   C1   D1
     1  -B2  -A2   A2   B2   C2   D2
     2  -B3  -A3   A3   B3   C3   D3
     3  -B4  -A4   A4   B4   C4   D4

    # To generate the table above
    index = range(-2, 4)
    row = '   ' + ' '.join([str(i).rjust(4) for i in index])
    print(row)
    for y in index:
        row = str(y).rjust(2) + ' ' + ' '.join([location2node((x, y)).rjust(4) for x in index])
        print(row)

    def check(node):
        return point2str(*node2location(location2node(node)), length=2)
    row = '   ' + ' '.join([str(i).rjust(8) for i in index])
    print(row)
    for y in index:
        row = str(y).rjust(2) + ' ' + ' '.join([check((x, y)).rjust(4) for x in index])
        print(row)

    Args:
        location (tuple[int]):

    Returns:
        str:
    """
    x, y = location
    if y >= 0:
        y += 1
    return col2name(x) + str(y)


def xywh2xyxy(area):
    """
    Convert (x, y, width, height) to (x1, y1, x2, y2)
    """
    x, y, w, h = area
    return x, y, x + w, y + h


def xyxy2xywh(area):
    """
    Convert (x1, y1, x2, y2) to (x, y, width, height)
    """
    x1, y1, x2, y2 = area
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
