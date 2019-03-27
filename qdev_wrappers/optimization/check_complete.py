

def num_attempts_reached(self, num_attempts):
    if num_attempts >= self.max_attempts:
        return True
    else:
        return False


def threshold_reached(self, num_attempts, best_cost_val, threshold):
    if num_attempts >= self.max_attempts:
        return True
    elif best_cost_val <= threshold:
        return True
    else:
        return False
