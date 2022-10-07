def action_point_redirect(value):
    """
    redirect attr about action point.
    """
    if value == 'false':
        return '0'
    elif value == 'true':
        return '5'
    else:
        return '0'
