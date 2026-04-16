import re
from importlib import import_module


def _models_module():
    return import_module('models')


def get_player():
    return _models_module().Player.query.first()


def add_inventory_item(player, item_id):
    models = _models_module()
    db = models.db
    Item = models.Item
    ItemType = models.ItemType

    source_item = Item.query.get(item_id)
    if source_item:
        item_type_id = source_item.item_type_id
        level = source_item.level
        is_loot = source_item.is_loot
    else:
        source_item_type = ItemType.query.get(item_id)
        if not source_item_type:
            return None
        item_type_id = source_item_type.id
        level = 1
        is_loot = False

    inventory_item = Item(
        item_type_id=item_type_id,
        owner_id=player.id,
        level=level,
        is_equipped=False,
        is_loot=is_loot,
    )
    db.session.add(inventory_item)
    return inventory_item


def remove_inventory_item(player, item_id):
    Item = _models_module().Item

    inventory_item = Item.query.filter_by(owner_id=player.id, is_equipped=False, id=item_id).first()
    if not inventory_item:
        inventory_item = Item.query.filter_by(owner_id=player.id, is_equipped=False, item_type_id=item_id).first()
    if not inventory_item:
        return None

    _models_module().db.session.delete(inventory_item)
    return inventory_item


def clear_player_inventory(player):
    _models_module().Item.query.filter_by(owner_id=player.id, is_equipped=False).delete()


def clear_player_equipment(player):
    _models_module().Item.query.filter_by(owner_id=player.id, is_equipped=True).delete()


def parse_item_upgrade_level(item_name):
    match = re.search(r"\s\+(\d+)$", item_name or '')
    if not match:
        return item_name or '', 0

    return item_name[:match.start()].strip(), int(match.group(1))


def get_upgraded_item(item):
    models = _models_module()
    db = models.db
    Item = models.Item
    ItemType = models.ItemType

    source_type = item.item_type if getattr(item, 'item_type', None) else ItemType.query.get(item.item_type_id)
    if not source_type:
        return None

    base_name, current_level = parse_item_upgrade_level(source_type.name)
    new_level = current_level + 1
    upgraded_name = f"{base_name} +{new_level}"

    upgraded_item_type = ItemType.query.filter_by(name=upgraded_name).first()
    if not upgraded_item_type:
        upgraded_item_type = ItemType(
            name=upgraded_name,
            description=(source_type.description or '') + f' (Reforged +{new_level})',
            bonus_attack=(source_type.bonus_attack or 0) * 2,
            bonus_health=(source_type.bonus_health or 0) * 2,
        )
        db.session.add(upgraded_item_type)
        db.session.commit()

    upgraded_item = Item(
        item_type_id=upgraded_item_type.id,
        owner_id=item.owner_id,
        level=new_level,
        is_equipped=False,
        is_loot=item.is_loot,
    )
    db.session.add(upgraded_item)
    db.session.commit()
    return upgraded_item