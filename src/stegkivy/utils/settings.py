class SteganoSettings:
    def __init__(self):
        self.encoding = 'utf-8'
        self.compression = True  # Whether to compress data before hiding
        self.encryption_key = None  # Optional encryption key
