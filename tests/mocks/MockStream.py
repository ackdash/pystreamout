from typing import BinaryIO
import time


class MockStream(BinaryIO):
    def __init__(self, data=None):
        super()
        self.mock_data = []
        self.mock_data_index = 0
        self.readline_index = 0
        self.should_close = False
        self.delay_duration = 0

        if data is not None:
            self.set_data(data=data)

    def set_data(self, data=None):
        self.mock_data = [] if data is None else data

        if len(self.mock_data) > 0:
            next(self)

    def readline(self):
        if len(self.mock_data) > 0 and len(self.mock_current_data):
            next_value = next(self.mock_current_data_iter)

            if next_value == b"":
                next(self)

            return next_value
        else:
            raise ValueError

    def __iter__(self):
        return self

    def set_delay(self, *, delay):
        self.delay_duration = delay

    def __next__(self):
        if self.mock_data_index < len(self.mock_data):
            self.mock_current_data = self.mock_data[self.mock_data_index]
            self.mock_current_data_iter = iter(self.mock_current_data)
            self.mock_data_index += 1

            time.sleep(self.delay_duration)
        else:
            self.should_close = True
        return self
