"""Hypermedia helpers for API response payloads."""

from __future__ import annotations

from typing import Any

from backend.db.models import Character, Combat, Item, User


def _copy_with_links(
    payload: dict[str, Any],
    links: dict[str, dict[str, list[str] | str]],
) -> dict[str, Any]:
    """Return a shallow copy with the supplied links attached."""
    response = dict(payload)
    response['_links'] = links
    return response


def _is_user_payload(payload: dict[str, Any]) -> bool:
    return {'id', 'username', 'state'}.issubset(payload)


def _is_character_payload(payload: dict[str, Any]) -> bool:
    return {'id', 'user_id', 'experience_to_next_level', 'bonus_damage', 'bonus_health'}.issubset(payload)


def _is_item_payload(payload: dict[str, Any]) -> bool:
    return {'id', 'item_type_id', 'slot_type', 'health', 'damage'}.issubset(payload)


def _is_combat_payload(payload: dict[str, Any]) -> bool:
    return {'id', 'character_id', 'character_health', 'enemy'}.issubset(payload)


def inject_response_links(
    payload: Any,
    *,
    user_id: int | None = None,
    character_id: int | None = None,
    character_state: Any | None = None,
    equipped: bool = False,
) -> Any:
    """Inject hypermedia links into supported API response payloads."""
    if isinstance(payload, list):
        return [
            inject_response_links(
                item,
                user_id=user_id,
                character_id=character_id,
                character_state=character_state,
                equipped=equipped,
            )
            for item in payload
        ]

    if not isinstance(payload, dict):
        return payload

    response = {
        key: inject_response_links(
            value,
            user_id=user_id,
            character_id=character_id,
            character_state=character_state,
            equipped=equipped,
        )
        if isinstance(value, (dict, list))
        else value
        for key, value in payload.items()
    }

    response.pop('links', None)

    if _is_user_payload(response):
        return _copy_with_links(response, User.response_links(response['id']))

    if _is_character_payload(response):
        return _copy_with_links(
            response,
            Character.response_links(response['id'], response['user_id'], state=response['state']),
        )

    if _is_item_payload(response):
        return _copy_with_links(
            response,
            Item.response_links(
                response['id'],
                user_id,
                character_id=character_id,
                character_state=character_state,
                equipped=equipped,
            ),
        )

    if _is_combat_payload(response):
        return _copy_with_links(response, Combat.response_links(response['id'], response['character_id']))

    return response


def inject_collection_links(
    payload: list[dict[str, Any]],
    *,
    user_id: int | None = None,
    character_id: int | None = None,
    character_state: Any | None = None,
    equipped: bool = False,
) -> list[dict[str, Any]]:
    """Inject links into each item in a collection payload."""
    return [
        inject_response_links(
            item,
            user_id=user_id,
            character_id=character_id,
            character_state=character_state,
            equipped=equipped,
        )
        if isinstance(item, dict)
        else item
        for item in payload
    ]