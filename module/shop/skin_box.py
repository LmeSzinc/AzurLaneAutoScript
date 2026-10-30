"""Configuration parsing for fixed General Shop skin-box positions."""
import re
import unicodedata


ALL_SKIN_BOX_SLOTS = frozenset(range(1, 11))


def parse_skin_box_slots(value):
    """Return row-major slot numbers, rejecting invalid explicit selections.

    The GUI supplies a canonical string; integer values also occur after the
    normal configuration parser reads a single selected slot.
    """
    if isinstance(value, bool):
        raise ValueError('A skin-box slot must be a number from 1 to 10')
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        raise ValueError('Invalid skin-box slot selection')
    value = unicodedata.normalize('NFKC', value).strip().lower().replace('、', ',')
    if value == 'all':
        return ALL_SKIN_BOX_SLOTS
    if value == 'none':
        return frozenset()
    if value.startswith('(') and value.endswith(')') or value.startswith('[') and value.endswith(']'):
        value = value[1:-1].strip()
    if not re.fullmatch(r'\d+\s*(?:,\s*\d+\s*)*', value):
        raise ValueError('Invalid skin-box slot selection')
    slots = frozenset(int(part.strip()) for part in value.split(','))
    if not slots or not slots <= ALL_SKIN_BOX_SLOTS:
        raise ValueError('Skin-box slot numbers must be from 1 to 10')
    return slots


def skin_box_counter(value):
    """Read a nonnegative operation count without silently removing a limit."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('Skin-box counters must be nonnegative integers')
    return value
