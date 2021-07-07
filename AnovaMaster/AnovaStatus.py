class AnovaStatus(object):
    def __init__(self):
        self.temp_unit = "C"
        self.current_temp = "0"
        self.target_temp = "0"
        self.state = "disconnected"

class AnovaTimerStatus(object):
    def __init__(self):
        self.timer = "0"
        self.timer_state = False
