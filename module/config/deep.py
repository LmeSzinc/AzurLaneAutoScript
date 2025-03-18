from collections import deque

# deep_* functions are used for access nested dictionary.
# They target for high performance so code are complicated to read
# In general performance practise, time costs are as below:
# - When key exists
#   try: dict[key] except KeyError << dict.get(key) < if key in dict: dict[key]
# - When not key exists
#   if key in dict: dict[key] < dict.get(key) <<< try: dict[key] except KeyError

OP_ADD = 'add'
OP_SET = 'set'
OP_DEL = 'del'


def deep_get(d, keys, default=None):
    """
    Get value from nested dict and list
    https://stackoverflow.com/questions/25833613/safe-method-to-get-value-of-nested-dictionary

    Args:
        d (dict):
        keys (list[str], str): Such as ['Scheduler', 'NextRun', 'value']
        default: Default return if key not found.

    Returns:
        Value on given keys
    """
    # 240 + 30 * depth (ns)
    if type(keys) is str:
        keys = keys.split('.')

    try:
        for k in keys:
            d = d[k]
        return d
    # No such key
    except KeyError:
        return default
    # No such key
    except IndexError:
        return default
    # Input `keys` is not iterable or input `d` is not dict
    # list indices must be integers or slices, not str
    except TypeError:
        return default


def deep_get_with_error(d, keys):
    """
    Get value from nested dict and list, raise KeyError if key not exists

    Args:
        d (dict):
        keys (list[str], str): Such as ['Scheduler', 'NextRun', 'value']

    Returns:
        Value on given keys

    Raises:
        KeyError: If key not exists
    """
    # 240 + 30 * depth (ns)
    if type(keys) is str:
        keys = keys.split('.')

    try:
        for k in keys:
            d = d[k]
        return d
    # No such key
    # except KeyError:
    #     raise
    # No such key
    except IndexError:
        raise KeyError
    # Input `keys` is not iterable or input `d` is not dict
    # list indices must be integers or slices, not str
    except TypeError:
        raise KeyError


def deep_exist(d, keys):
    """
    Check if keys exists in nested dict or list

    Args:
        d (dict):
        keys (str, list): Such as `Scheduler.NextRun.value`

    Returns:
        bool: If key exists
    """
    # 240 + 30 * depth (ns)
    if type(keys) is str:
        keys = keys.split('.')

    try:
        for k in keys:
            d = d[k]
        return True
    # No such key
    except KeyError:
        return False
    # No such key
    except IndexError:
        return False
    # Input `keys` is not iterable or input `d` is not dict
    # list indices must be integers or slices, not str
    except TypeError:
        return False


def deep_set(d, keys, value):
    """
    Set value into nested dict safely, imitating deep_get().
    Can only set dict
    """
    # 150 * depth (ns)
    if type(keys) is str:
        keys = keys.split('.')

    first = True
    exist = True
    prev_d = None
    prev_k = None
    prev_k2 = None
    try:
        for k in keys:
            if first:
                prev_d = d
                prev_k = k
                first = False
                continue
            try:
                # if key in dict: dict[key] > dict.get > dict.setdefault > try dict[key] except
                if exist and prev_k in d:
                    prev_d = d
                    d = d[prev_k]
                else:
                    exist = False
                    new = {}
                    d[prev_k] = new
                    d = new
            except TypeError:
                # `d` is not dict
                exist = False
                d = {}
                prev_d[prev_k2] = {prev_k: d}

            prev_k2 = prev_k
            prev_k = k
            # prev_k2, prev_k = prev_k, k
    # Input `keys` is not iterable
    except TypeError:
        return

    # Last key, set value
    try:
        d[prev_k] = value
        return
    # Last value `d` is not dict
    except TypeError:
        prev_d[prev_k2] = {prev_k: value}
        return


def deep_default(d, keys, value):
    """
    Set value into nested dict safely, imitating deep_get().
    Can only set dict
    """
    # 150 * depth (ns)
    if type(keys) is str:
        keys = keys.split('.')

    first = True
    exist = True
    prev_d = None
    prev_k = None
    prev_k2 = None
    try:
        for k in keys:
            if first:
                prev_d = d
                prev_k = k
                first = False
                continue
            try:
                # if key in dict: dict[key] > dict.get > dict.setdefault > try dict[key] except
                if exist and prev_k in d:
                    prev_d = d
                    d = d[prev_k]
                else:
                    exist = False
                    new = {}
                    d[prev_k] = new
                    d = new
            except TypeError:
                # `d` is not dict
                exist = False
                d = {}
                prev_d[prev_k2] = {prev_k: d}

            prev_k2 = prev_k
            prev_k = k
            # prev_k2, prev_k = prev_k, k
    # Input `keys` is not iterable
    except TypeError:
        return

    # Last key, set value
    try:
        d.setdefault(prev_k, value)
        return
    # Last value `d` is not dict
    except AttributeError:
        prev_d[prev_k2] = {prev_k: value}
        return


def deep_pop(d, keys, default=None):
    """
    Pop value from nested dict and list
    """
    if type(keys) is str:
        keys = keys.split('.')

    try:
        for k in keys[:-1]:
            d = d[k]
        # No `pop(k, default)` so it can pop list
        return d.pop(keys[-1])
    # No such key
    except KeyError:
        return default
    # Input `keys` is not iterable or input `d` is not dict
    # list indices must be integers or slices, not str
    except TypeError:
        return default
    # Input `keys` out of index
    except IndexError:
        return default
    # Last `d` is not dict
    except AttributeError:
        return default


def deep_iter_depth1(data):
    """
    Equivalent to data.items() but suppress error if data is not a dict

    Args:
        data:

    Yields:
        Any: Key
        Any: Value
    """
    try:
        for k, v in data.items():
            yield k, v
        return
    except AttributeError:
        # `data` is not dict
        return


def deep_iter_depth2(data):
    """
    Iter key and value in nested dict of depth 2
    A simplified deep_iter

    Args:
        data:

    Yields:
        Any: Key1
        Any: Key2
        Any: Value
    """
    try:
        for k1, v1 in data.items():
            if type(v1) is dict:
                for k2, v2 in v1.items():
                    yield k1, k2, v2
    except AttributeError:
        # `data` is not dict
        return


def deep_iter(data, min_depth=None, depth=3):
    """
    Iter key and value in nested dict
    300us on alas.json depth=3 (530+ rows)
    Can only iter dict

    Args:
        data:
        min_depth:
        depth:

    Yields:
        list[str]: Key path
        Any: Value
    """
    if min_depth is None:
        min_depth = depth
    assert 1 <= min_depth <= depth

    # Equivalent to dict.items()
    try:
        if depth == 1:
            for k, v in data.items():
                yield [k], v
            return
        # Iter first depth
        elif min_depth == 1:
            q = deque()
            for k, v in data.items():
                key = [k]
                if type(v) is dict:
                    q.append((key, v))
                else:
                    yield key, v
        # Iter target depth only
        else:
            q = deque()
            for k, v in data.items():
                key = [k]
                if type(v) is dict:
                    q.append((key, v))
    except AttributeError:
        # `data` is not dict
        return

    # Iter depths
    current = 2
    while current <= depth:
        new_q = deque()
        # max depth
        if current == depth:
            for key, data in q:
                for k, v in data.items():
                    yield key + [k], v
        # in target depth
        elif min_depth <= current < depth:
            for key, data in q:
                for k, v in data.items():
                    subkey = key + [k]
                    if type(v) is dict:
                        new_q.append((subkey, v))
                    else:
                        yield subkey, v
        # Haven't reached min depth
        else:
            for key, data in q:
                for k, v in data.items():
                    subkey = key + [k]
                    if type(v) is dict:
                        new_q.append((subkey, v))
        q = new_q
        current += 1


def deep_values(data, min_depth=None, depth=3):
    """
    Iter value in nested dict
    300us on alas.json depth=3 (530+ rows)
    Can only iter dict

    Args:
        data:
        min_depth:
        depth:

    Yields:
        Any: Value
    """
    if min_depth is None:
        min_depth = depth
    assert 1 <= min_depth <= depth

    # Equivalent to dict.items()
    try:
        if depth == 1:
            for v in data.values():
                yield v
            return
        # Iter first depth
        elif min_depth == 1:
            q = deque()
            for v in data.values():
                if type(v) is dict:
                    q.append(v)
                else:
                    yield v
        # Iter target depth only
        else:
            q = deque()
            for v in data.values():
                if type(v) is dict:
                    q.append(v)
    except AttributeError:
        # `data` is not dict
        return

    # Iter depths
    current = 2
    while current <= depth:
        new_q = deque()
        # max depth
        if current == depth:
            for data in q:
                for v in data.values():
                    yield v
        # in target depth
        elif min_depth <= current < depth:
            for data in q:
                for v in data.values():
                    if type(v) is dict:
                        new_q.append(v)
                    else:
                        yield v
        # Haven't reached min depth
        else:
            for data in q:
                for v in data.values():
                    if type(v) is dict:
                        new_q.append(v)
        q = new_q
        current += 1


def deep_iter_diff(before, after):
    """
    Iter diff between 2 dict.
    Pretty fast to compare 2 deeply nested dict,
    time cost increases with the number of differences.

    Args:
        before:
        after:

    Yields:
        list[str]: Key path
        Any: Value in before, or None if not exists
        Any: Value in after, or None if not exists
    """
    if before == after:
        return
    if type(before) is not dict or type(after) is not dict:
        yield [], before, after
        return

    queue = deque([([], before, after)])
    while True:
        new_queue = deque()
        for path, d1, d2 in queue:
            keys1 = set(d1.keys())
            keys2 = set(d2.keys())
            for key in keys1.union(keys2):
                try:
                    val2 = d2[key]
                except KeyError:
                    # Safe to access d1[key], because key came from the union of both
                    # If it's not in d2 then it's in d1
                    yield path + [key], d1[key], None
                    continue
                try:
                    val1 = d1[key]
                except KeyError:
                    yield path + [key], None, val2
                    continue
                # Compare dict first, which is pretty fast
                if val1 != val2:
                    if type(val1) is dict and type(val2) is dict:
                        new_queue.append((path + [key], val1, val2))
                    else:
                        yield path + [key], val1, val2
        queue = new_queue
        if not queue:
            break


def deep_iter_patch(before, after):
    """
    Iter patch event from before to after, like creating a json-patch
    Pretty fast to compare 2 deeply nested dict,
    time cost increases with the number of differences.

    Args:
        before:
        after:

    Yields:
        str: OP_ADD, OP_SET, OP_DEL
        list[str]: Key path
        Any: Value in after,
            or None of event is OP_DEL
    """
    if before == after:
        return
    if type(before) is not dict or type(after) is not dict:
        yield OP_SET, [], after
        return

    queue = deque([([], before, after)])
    while True:
        new_queue = deque()
        for path, d1, d2 in queue:
            keys1 = set(d1.keys())
            keys2 = set(d2.keys())
            for key in keys1.union(keys2):
                try:
                    val2 = d2[key]
                except KeyError:
                    yield OP_DEL, path + [key], None
                    continue
                try:
                    val1 = d1[key]
                except KeyError:
                    yield OP_ADD, path + [key], val2
                    continue
                # Compare dict first, which is pretty fast
                if val1 != val2:
                    if type(val1) is dict and type(val2) is dict:
                        new_queue.append((path + [key], val1, val2))
                    else:
                        yield OP_SET, path + [key], val2
        queue = new_queue
        if not queue:
            break
