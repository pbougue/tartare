
class DataSetFetcher(object):
    def __init__(self, data_sources, context):
        self.data_sources = data_sources
        self.context = context

    def fetch(self):
        for d in self.data_sources:
            data_input = d.get('input')
            if data_input:
                input_type = d.get('type')
                if input_type == 'url':
                    # HTTP GET input.get('url')
                    self.context[d.id] = "file path"
        return self.context
