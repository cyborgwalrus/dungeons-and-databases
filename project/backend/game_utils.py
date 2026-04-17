import re

from flask import session
from flask_login import current_user

from .db.models import Character, Item, ItemType, db


PLAYER_SESSION_KEY = 'character_id'
DEFAULT_LOADOUT_ITEM_NAMES = [
    'Steel Sword',
    'Steel Sword',
    'Leather Armor',
    'Steel Armor',
    'Iron Shield',
    'Iron Helmet',
    'Silver Necklace',
    'Enchanted Ring',
]


def apply_item_type_stats(item: Item, item_type: ItemType) -> Item:
    item.name = item_type.name
    item.health_bonus = item_type.base_health_bonus or 0
    item.damage_bonus = item_type.base_damage_bonus or 0
    return item


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
    for item_name in DEFAULT_LOADOUT_ITEM_NAMES:
        item_type = ItemType.query.filter_by(name=item_name).first()
        if item_type:
            add_inventory_item(character, item_type.id)


def add_inventory_item(player: Character, item_id: int) -> Item | None:
    item_model = Item
    item_type_model = ItemType

    source_item = item_model.query.get(item_id)
    if source_item:
        item_type = source_item.item_type or item_type_model.query.get(source_item.item_type_id)
        level = source_item.level
        is_loot = source_item.is_loot
    else:
        item_type = item_type_model.query.get(item_id)
        if not item_type:
            return None
        level = 1
        is_loot = False

    if not item_type:
        return None

    inventory_item = item_model(
        name=item_type.name,
        item_type_id=item_type.id,
        owner_id=player.id,
        level=level,
        health_bonus=item_type.base_health_bonus or 0,
        damage_bonus=item_type.base_damage_bonus or 0,
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


def get_upgraded_item(item: Item) -> Item | None:
    item_model = Item
    item_type_model = ItemType

    source_type = item.item_type if getattr(item, 'item_type', None) else item_type_model.query.get(item.item_type_id)
    if not source_type:
        return None

    base_name = re.sub(r'\s\+\d+$', '', item.name or source_type.name).strip()
    new_level = (item.level or 0) + 1
    upgraded_name = f"{base_name} +{new_level}"

    upgraded_item_type = item_type_model.query.filter_by(name=upgraded_name).first()
    if not upgraded_item_type:
        upgraded_item_type = item_type_model(
            name=upgraded_name,
            slot=source_type.slot,
            base_damage_bonus=(getattr(source_type, 'base_damage_bonus', 0) or 0) * 2,
            base_health_bonus=(getattr(source_type, 'base_health_bonus', 0) or 0) * 2,
        )
        db.session.add(upgraded_item_type)
        db.session.commit()

    upgraded_item = item_model(
        item_type_id=upgraded_item_type.id,
        owner_id=item.owner_id,
        level=new_level,
        is_equipped=False,
        is_loot=item.is_loot,
    )
    apply_item_type_stats(upgraded_item, upgraded_item_type)
    db.session.add(upgraded_item)
    db.session.commit()
    return upgraded_item