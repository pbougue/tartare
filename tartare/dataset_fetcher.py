from abc import ABCMeta, abstractmethod


class AbstractDataSetFetcher(metaclass=ABCMeta):
    @abstractmethod
    def fetch(self):
        pass


class HttpDataSetFetcher(AbstractDataSetFetcher):
    def __init__(self, data_source, context):
        self.data_source = data_source
        self.context = context

    def fetch(self):
        data_input = self.data_source.get('input')
        if data_input:
                # HTTP GET input.get('url')
                self.context.update({self.data_source.id: "file path"})
        return self.context


class FtpDataSetFetcher(AbstractDataSetFetcher):
    def __init__(self, data_source, context):
        self.data_source = data_source
        self.context = context

    def fetch(self):
        data_input = self.data_source.get('input')
        if data_input:
                # FTP GET input.get('url')
                self.context.update({self.data_source.id: "file path"})
        return self.context
