class BudgetAppError(Exception):
    def __init__(self, message: str, hint: str):
        super().__init__(message)
        self.message = message
        self.hint = hint

class ValidationError(BudgetAppError):
    pass

class DataStoreError(BudgetAppError):
    pass

class NotFoundError(BudgetAppError):
    pass
