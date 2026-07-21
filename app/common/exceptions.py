from fastapi import HTTPException, status

class CommerceFlowException(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.message = message

class BadRequestException(CommerceFlowException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message)

class UnauthorizedException(CommerceFlowException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message)

class ResourceNotFoundException(CommerceFlowException):
    def __init__(self, resource_name: str, field_name: str, field_value: any):
        message = f"{resource_name} not found with {field_name}: '{field_value}'"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message)

class ForbiddenException(CommerceFlowException):
    def __init__(self, message: str = "Access Denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message)
