import re
from importlib import import_module


def _database_module():
    return import_module('database')


def _models_module():
    return import_module('models')


def get_player():
    return _models_module().Player.query.first()


def add_inventory_item(player, item_id):
    db = _database_module().db
    InventoryItem = _models_module().InventoryItem

    inventory_item = InventoryItem(player_id=player.id, item_id=item_id)
    db.session.add(inventory_item)
    return inventory_item


def remove_inventory_item(player, item_id):
    InventoryItem = _models_module().InventoryItem

    inventory_item = InventoryItem.query.filter_by(player_id=player.id, item_id=item_id).first()
    if not inventory_item:
        return None

    _database_module().db.session.delete(inventory_item)
    return inventory_item


def clear_player_inventory(player):
    _models_module().InventoryItem.query.filter_by(player_id=player.id).delete()


def clear_player_equipment(player):
    _models_module().EquippedItem.query.filter_by(player_id=player.id).delete()


def parse_item_upgrade_level(item_name):
    match = re.search(r"\s\+(\d+)$", item_name or '')
    if not match:
        return item_name or '', 0

    return item_name[:match.start()].strip(), int(match.group(1))


def get_upgraded_item(item):
    db = _database_module().db
    Item = _models_module().Item

    base_name, current_level = parse_item_upgrade_level(item.name)
    new_level = current_level + 1
    upgraded_name = f"{base_name} +{new_level}"

    upgraded_item = Item.query.filter_by(name=upgraded_name).first()
    if upgraded_item:
        return upgraded_item

    upgraded_item = Item(
        name=upgraded_name,
        description=(item.description or '') + f' (Reforged +{new_level})',
        bonus_attack=(item.bonus_attack or 0) * 2,
        bonus_health=(item.bonus_health or 0) * 2
    )
    db.session.add(upgraded_item)
    db.session.commit()
    return upgraded_item