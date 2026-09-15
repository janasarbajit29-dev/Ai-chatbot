from pydantic import BaseModel, EmailStr, model_validator
from datetime import date

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    date_of_birth: date

    @model_validator(mode="after")
    def check_passwords_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self
