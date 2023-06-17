def handle_sensitive_image(image):
    """
    Args:
        image:

    Returns:
        np.ndarray:
    """
    # Paint UID to black
    image[680:720, 0:180, :] = 0
    return image


def handle_sensitive_logs(logs):
    return logs
