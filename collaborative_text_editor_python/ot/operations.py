class Reverted(object):
    def __init__(self, action):
        self.action = action._reverted()
        self._is_reverted = True

    def apply(self, data):
        self.action.apply(data)

class Noop(object):
    def apply(self, data):
        pass

    def _reverted(self):
        return self

class Compose(object):
    def __init__(self, operations):
        self.operations = operations

    def apply(self, data):
        for operation in self.operations:
            operation.apply(data)

    def _reverted(self):
        return Compose(map(Reverted, reversed(self.operations)))

class Remove(object):
    def __init__(self, position, value):
        self.position = position
        self.value = value

    def apply(self, data):
        assert data[self.position] == self.value
        data.pop(self.position)

    def _reverted(self):
        return Add(self.position, self.value)

class Add(object):
    def __init__(self, position, value):
        self.position = position
        self.value = value

    def apply(self, data):
        data.insert(self.position, self.value)

    def _reverted(self):
        return Remove(self.position, self.value)
