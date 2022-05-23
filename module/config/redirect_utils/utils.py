def upload_redirect(value):
    """
    redirect attr about upload.
    """
    if isinstance(value, list):
        if not value[0] and not value[1]:
            return 'do_not'
        elif value[0] and not value[1]:
            return 'save'
        elif not value[0] and value[1]:
            return 'upload'
        else:
            return 'save_and_upload'
    else:
        if not value:
            return 'do_not'
        else:
            return 'save'


def api_redirect(value):
    """
    redirect attr about api.
    """
    if value != 'com.YoStarEN.AzurLane' and \
            value != 'com.YoStarJP.AzurLane' and \
            value != 'com.hkmanjuu.azurlane.gp.mc' and \
            value != 'com.hkmanjuu.azurlane.gp' and \
            value != 'auto':
        return 'cn_reverse_proxy'
    else:
        return 'default'
