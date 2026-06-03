"""
Circle.so community adapter.
API: https://app.circle.so/api/v1
Auth: Token <api_key> header
"""
import httpx
from typing import Any
from adapters.community.base import CommunityAdapter, CommunityMember

CIRCLE_BASE = "https://app.circle.so/api/v1"


class CircleAdapter(CommunityAdapter):

    def __init__(self, api_key: str, community_id: str):
        self.community_id = community_id
        self._client = httpx.AsyncClient(
            base_url=CIRCLE_BASE,
            headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
            timeout=15.0,
        )

    @property
    def platform_name(self) -> str:
        return "circle"

    async def _get(self, path: str, **params) -> Any:
        r = await self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, data: dict) -> Any:
        r = await self._client.post(path, json=data)
        r.raise_for_status()
        return r.json()

    async def _put(self, path: str, data: dict) -> Any:
        r = await self._client.put(path, json=data)
        r.raise_for_status()
        return r.json()

    async def _delete(self, path: str) -> bool:
        r = await self._client.delete(path)
        return r.status_code in (200, 204)

    async def get_member_by_email(self, email: str) -> CommunityMember | None:
        try:
            data = await self._get("/community_members",
                                   community_id=self.community_id, email=email)
            members = data if isinstance(data, list) else data.get("community_members", [])
            if not members:
                return None
            m = members[0]
            return CommunityMember(
                platform_user_id=str(m["id"]),
                email=m.get("email", email),
                name=m.get("name"),
                role=m.get("role"),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def invite_member(
        self, email: str, name: str | None = None,
        role: str | None = None, space_ids: list[str] | None = None,
    ) -> CommunityMember:
        payload: dict[str, Any] = {
            "community_id": self.community_id,
            "email": email,
            "skip_invitation": False,
        }
        if name:          payload["name"]      = name
        if role:          payload["role"]      = role
        if space_ids:     payload["space_ids"] = space_ids

        data = await self._post("/community_members", payload)
        return CommunityMember(
            platform_user_id=str(data["id"]),
            email=data.get("email", email),
            name=data.get("name"),
            role=data.get("role"),
        )

    async def remove_member(self, platform_user_id: str) -> bool:
        return await self._delete(
            f"/community_members/{platform_user_id}?community_id={self.community_id}"
        )

    async def change_member_role(self, platform_user_id: str, new_role: str) -> bool:
        await self._put(f"/community_members/{platform_user_id}",
                        {"community_id": self.community_id, "role": new_role})
        return True

    async def add_member_to_spaces(self, platform_user_id: str, space_ids: list[str]) -> bool:
        for sid in space_ids:
            await self._post("/space_members", {
                "community_id":        self.community_id,
                "space_id":            sid,
                "community_member_id": platform_user_id,
            })
        return True

    async def remove_member_from_spaces(self, platform_user_id: str, space_ids: list[str]) -> bool:
        for sid in space_ids:
            await self._delete(
                f"/space_members/{platform_user_id}"
                f"?community_id={self.community_id}&space_id={sid}"
            )
        return True

    async def close(self):
        await self._client.aclose()
