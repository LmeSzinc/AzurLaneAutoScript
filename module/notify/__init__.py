def handle_notify(*args, **kwargs):
    # Lazy import onepush
    from module.notify.notify import handle_notify
    return handle_notify(*args, **kwargs)
