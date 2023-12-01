from datetime import datetime


nan = float("nan")


class StreamObject:
    def set_by_name(self, attr_name, values, key, type):
        try:
            if key in values:
                setattr(self, attr_name, type(values[key]))
        except TypeError:
            # ignore, there will be plenty of dud values
            pass

    def set_timestamp_by_name(self, attr_name, values, key):
        try:
            if key in values:
                setattr(
                    self, attr_name, datetime.fromtimestamp(int(values[key]) / 1000)
                )
        except TypeError:
            # ignore, there will be plenty of dud values
            pass
