from typing import List, Union

class InputStep:
    """Represents a single step in a keyboard sequence.
    Can press multiple keys simultaneously and hold them for a given duration of frames.
    """
    def __init__(self, keys: Union[str, List[str]], duration_frames: int):
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = list(keys)
        self.duration_frames = duration_frames

    def __repr__(self):
        return f"InputStep(keys={self.keys}, duration_frames={self.duration_frames})"


class InputSequence:
    """Represents a complete combo or input sequence, composed of multiple InputSteps."""
    def __init__(self, name: str, steps: List[InputStep]):
        self.name = name
        self.steps = steps

    def __repr__(self):
        return f"InputSequence(name='{self.name}', steps={self.steps})"
