from database import db
from models import EquippedItem, InventoryItem, Player


def get_player():
    return Player.query.first()


def adjust_inventory_quantity(player, item_id, delta):
    inventory_item = InventoryItem.query.filter_by(player_id=player.id, item_id=item_id).first()

    if delta > 0:
        if inventory_item:
            inventory_item.quantity += delta
        else:
            inventory_item = InventoryItem(player_id=player.id, item_id=item_id, quantity=delta)
            db.session.add(inventory_item)
        return inventory_item

    if not inventory_item:
        return None

    quantity_to_remove = abs(delta)
    if inventory_item.quantity > quantity_to_remove:
        inventory_item.quantity -= quantity_to_remove
    else:
        db.session.delete(inventory_item)

    return inventory_item


def clear_player_inventory(player):
    InventoryItem.query.filter_by(player_id=player.id).delete()


def clear_player_equipment(player):
    EquippedItem.query.filter_by(player_id=player.id).delete()