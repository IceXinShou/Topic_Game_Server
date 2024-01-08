class BadRequestError(Exception):
    def __init__(self, message: str):
        print(message)
