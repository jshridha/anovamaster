class StatusException(Exception):
    def __init__(self, state):
        self.state = state
