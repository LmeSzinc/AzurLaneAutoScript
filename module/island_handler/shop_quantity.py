"""Dependency-free quantity selection for the Island Shop purchase dialog.

The shop may cap the selectable quantity below a temporary rounding target,
such as when only 19 seeds can be afforded but 18 are requested. Adjust only
toward the exact amount, checking the displayed quantity after each batch.
"""


def quantity_adjustment(current, target):
    """Return (button_name, clicks) without overshooting the desired quantity."""
    diff = target - current
    if diff >= 10:
        return 'plus_ten', min(diff // 10, 3)
    if diff > 0:
        return 'plus_one', min(diff, 3)
    if diff <= -10:
        return 'minus_ten', min(-diff // 10, 3)
    if diff < 0:
        return 'minus_one', min(-diff, 3)
    return None, 0


def ensure_purchase_quantity(target, read_amount, press):
    """Set an exact shop quantity; return False if a game-imposed cap stops it.

    read_amount() obtains the displayed count from a new screenshot.
    press(button_name, count) applies a small batch of +/-10 or +/-1 clicks.
    This helper deliberately has no ALAS imports, so behavior can be unit-tested
    without loading the emulator, OCR models, or image processing libraries.
    """
    if not isinstance(target, int) or target < 1:
        return False

    current = read_amount()
    if not isinstance(current, int) or current < 1:
        return False

    # At most three +/-10 clicks in a batch, followed by a fresh OCR check.
    max_batches = 10 + (abs(target - current) + 29) // 30
    for _ in range(max_batches):
        if current == target:
            return True
        button, clicks = quantity_adjustment(current, target)
        press(button, clicks)
        updated = read_amount()
        if not isinstance(updated, int) or updated < 1 or updated == current:
            return False
        current = updated

    return current == target
