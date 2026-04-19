from flask import session
from flask_login import current_user

from .cache_helpers import get_all_item_type_data, get_item_type_data
from ..db.models import Character, Item, db


PLAYER_SESSION_KEY = 'character_id'
DEFAULT_LOADOUT_ITEM_NAMES = [
    'Steel Sword',
    'Leather Armor',
    'Iron Shield',
    'Iron Helmet',
    'Silver Necklace',
    'Enchanted Ring',
]


def set_player(character_id: int | None) -> None:
    if character_id is None:
        session.pop(PLAYER_SESSION_KEY, None)
        return
    session[PLAYER_SESSION_KEY] = int(character_id)


def get_player() -> Character | None:
    character_id = session.get(PLAYER_SESSION_KEY)
    if character_id is None:
        return None

    try:
        resolved_character_id = int(character_id)
    except (TypeError, ValueError):
        session.pop(PLAYER_SESSION_KEY, None)
        return None

    character = Character.query.get(resolved_character_id)
    if not character:
        session.pop(PLAYER_SESSION_KEY, None)
        return None

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        if user_id and character.user_id != int(user_id):
            session.pop(PLAYER_SESSION_KEY, None)
            return None

    return character


def seed_character_loadout(character: Character) -> None:
    item_types_by_name = {item_type['name']: item_type for item_type in get_all_item_type_data()}
    for item_name in DEFAULT_LOADOUT_ITEM_NAMES:
        item_type = item_types_by_name.get(item_name)
        if item_type:
            add_inventory_item(character, item_type['id'], copy_from_item=False)


def add_inventory_item(player: Character, item_id: int, *, copy_from_item: bool = False) -> Item | None:
    item_model = Item

    source_item = item_model.query.get(item_id) if copy_from_item else None
    if source_item:
        item_type = get_item_type_data(source_item.item_type_id)
        level = source_item.level
        is_loot = source_item.is_loot
    else:
        item_type = get_item_type_data(item_id)
        if not item_type:
            return None
        level = 1
        is_loot = False

    if not item_type:
        return None

    inventory_item = item_model(
        name=item_type['name'],
        item_type_id=item_type['id'],
        owner_id=player.id,
        level=level,
        health_bonus=item_type['base_health_bonus'] or 0,
        damage_bonus=item_type['base_damage_bonus'] or 0,
        is_equipped=False,
        is_loot=is_loot,
    )
    db.session.add(inventory_item)
    return inventory_item


def remove_inventory_item(player: Character, item_id: int) -> Item | None:
    item_model = Item

    inventory_item = item_model.query.filter_by(owner_id=player.id, is_equipped=False, id=item_id).first()
    if not inventory_item:
        inventory_item = item_model.query.filter_by(owner_id=player.id, is_equipped=False, item_type_id=item_id).first()
    if not inventory_item:
        return None

    db.session.delete(inventory_item)
    return inventory_item


def clear_player_inventory(player: Character) -> None:
    Item.query.filter_by(owner_id=player.id, is_equipped=False).delete()


def clear_player_equipment(player: Character) -> None:
    Item.query.filter_by(owner_id=player.id, is_equipped=True).delete()
