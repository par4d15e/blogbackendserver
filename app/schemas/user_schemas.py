from pydantic import BaseModel, Field


class UserIDSchema(BaseModel):
    user_id: int


class BioRequest(BaseModel):
    bio: str = Field("大家好, 这是我的简介", min_length=1, max_length=255)


class EnableDisableUserRequest(UserIDSchema):
    is_active: bool = Field(
        default=False, description="Whether the user is active or not"
    )
