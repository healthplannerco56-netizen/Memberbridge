"""Abstract community platform adapter."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommunityMember:
    platform_user_id: str
    email: str
    name: str | None
    role: str | None


class CommunityAdapter(ABC):

    @property
    @abstractmethod
    def platform_name(self) -> str: ...

    @abstractmethod
    async def get_member_by_email(self, email: str) -> CommunityMember | None: ...

    @abstractmethod
    async def invite_member(
        self, email: str, name: str | None = None,
        role: str | None = None, space_ids: list[str] | None = None,
    ) -> CommunityMember: ...

    @abstractmethod
    async def remove_member(self, platform_user_id: str) -> bool: ...

    @abstractmethod
    async def change_member_role(self, platform_user_id: str, new_role: str) -> bool: ...

    @abstractmethod
    async def add_member_to_spaces(self, platform_user_id: str, space_ids: list[str]) -> bool: ...

    @abstractmethod
    async def remove_member_from_spaces(self, platform_user_id: str, space_ids: list[str]) -> bool: ...
