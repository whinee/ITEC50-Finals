import datetime
from typing import Annotated, Literal

import sqlalchemy as sa
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlmodel import Column, Field, SQLModel


class AllPhone(PhoneNumber):
    default_region_code = "PH"
    supported_regions: list[str] = []
    phone_format = "INTERNATIONAL"


class BaseUsers(SQLModel, table=False):
    username: str | None = None
    email: EmailStr
    contact_number: AllPhone
    professional_license_id: str | None = None
    password: str


class Users(BaseUsers, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    role: Annotated[
        list[Literal["patient", "professional"]],
        Field(sa_column=Column(sa.ARRAY(sa.TEXT), nullable=False)),
    ]
    created_at: Annotated[
        datetime.datetime,
        Field(sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=False)),
    ]
    updated_at: Annotated[
        datetime.datetime,
        Field(sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True)),
    ]
    disabled: Annotated[bool, Field(sa_column=Column(sa.BOOLEAN, nullable=False))]
