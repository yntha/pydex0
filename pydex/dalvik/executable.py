from datastream import DeserializingStream


class DexFile:
    def __init__(self, data: bytes):
        self.data = data
        self.stream = DeserializingStream(data)
