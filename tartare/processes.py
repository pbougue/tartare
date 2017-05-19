from abc import ABCMeta, abstractmethod


class AbstractProcess(metaclass=ABCMeta):
    @abstractmethod
    def do(self):
        pass


class Ruspell(AbstractProcess):
    def __init__(self, context):
        self.context = context

    def do(self):
        return self.context


class ComputeDirections(AbstractProcess):
    def __init__(self, context):
        self.context = context

    def do(self):
        return self.context


class HeadsignShortName(AbstractProcess):
    def __init__(self, context):
        self.context = context

    def do(self):
        return self.context
