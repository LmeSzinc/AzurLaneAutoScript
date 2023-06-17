class ServerChecker:
    # Create a fake server check since server check is not supported yet.
    def __init__(self, server):
        pass

    def check_now(self):
        pass

    def is_available(self):
        return True

    def wait_until_available(self):
        pass

    def is_recovered(self):
        return False
