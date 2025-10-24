from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="OAuthCallbackRequest")


@_attrs_define
class OAuthCallbackRequest:
    """OAuth2 callback request.

    Attributes:
        code (str): Authorization code from OAuth provider
        user_id (str): User ID to associate with credentials
        state (Union[None, Unset, str]): State parameter for CSRF validation
    """

    code: str
    user_id: str
    state: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        user_id = self.user_id

        state: None | Unset | str
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "user_id": user_id,
            }
        )
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        user_id = d.pop("user_id")

        def _parse_state(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        state = _parse_state(d.pop("state", UNSET))

        o_auth_callback_request = cls(
            code=code,
            user_id=user_id,
            state=state,
        )

        o_auth_callback_request.additional_properties = d
        return o_auth_callback_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
