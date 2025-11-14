from pydantic import BaseModel, Field


class EmailSchema(BaseModel):
    email: str = Field("ln729500172@gmail.com", description="Email address")


class CodeSchema(BaseModel):
    code: str = Field("123456", description="Verification code")


class PasswordSchema(BaseModel):
    password: str = Field("Ln8218270@", description="Password")


class UsernameSchema(BaseModel):
    username: str = Field("ningli3739", description="Username")


class SendCodeRequest(EmailSchema):
    pass


class CreateUserAccountRequest(CodeSchema, EmailSchema, PasswordSchema, UsernameSchema):
    pass


class ResetPasswordRequest(CodeSchema, EmailSchema, PasswordSchema):
    pass


class AccountLoginRequest(EmailSchema, PasswordSchema):
    pass


class ResetLoggedInUserPasswordRequest(PasswordSchema):
    pass
