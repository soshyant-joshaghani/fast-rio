from sqlmodel import Field, SQLModel


class Message(SQLModel):
    message: str


class PrivateUserCreate(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
