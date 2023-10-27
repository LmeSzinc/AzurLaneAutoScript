def action_point_redirect(value):
    """
    redirect attr about action point

    Args:
        value (bool):
          If Enable, return 5.
          If Disable, return 0.
    """
    if value is True:
        return 5
    else:
        return 0
