import itertools

from ppocronnx.predict_system import BoxedResult


def area_cross_area(area1, area2, thres_x=20, thres_y=20):
    """
    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        thres_x:
        thres_y:

    Returns:
        bool:
    """
    # https://www.yiiven.cn/rect-is-intersection.html
    xa1, ya1, xa2, ya2 = area1
    xb1, yb1, xb2, yb2 = area2
    return abs(xb2 + xb1 - xa2 - xa1) <= xa2 - xa1 + xb2 - xb1 + thres_x * 2 \
        and abs(yb2 + yb1 - ya2 - ya1) <= ya2 - ya1 + yb2 - yb1 + thres_y * 2


def _merge_area(area1, area2):
    xa1, ya1, xa2, ya2 = area1
    xb1, yb1, xb2, yb2 = area2
    return min(xa1, xb1), min(ya1, yb1), max(xa2, xb2), max(ya2, yb2)


def _merge_boxed_result(left: BoxedResult, right: BoxedResult) -> BoxedResult:
    left.box = _merge_area(left.box, right.box)
    left.ocr_text = left.ocr_text + right.ocr_text
    return left


def merge_buttons(buttons: list[BoxedResult], thres_x=20, thres_y=20) -> list[BoxedResult]:
    """
    Args:
        buttons:
        thres_x: Merge results with horizontal box distance <= `thres_x`
        thres_y: Merge results with vertical box distance <= `thres_y`

    Returns:

    """
    dic_button = {button.box: button for button in buttons}
    set_merged = set()
    for left, right in itertools.combinations(dic_button.items(), 2):
        left_box, left = left
        right_box, right = right
        if area_cross_area(left.box, right.box, thres_x=thres_x, thres_y=thres_y):
            left = _merge_boxed_result(left, right)
            dic_button[left_box] = left
            dic_button[right_box] = left
            set_merged.add(right_box)

    return [button for box, button in dic_button.items() if box not in set_merged]
