from flask import Blueprint, jsonify, request
from database import db
from models import Item, InventoryItem, EquippedItem
from game_utils import adjust_inventory_quantity, clear_player_inventory, get_player, get_upgraded_item

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get player inventory"""
    player = get_player()
    return jsonify(player.get_inventory())


@inventory_bp.route('/api/inventory/equipped', methods=['GET'])
def get_equipped():
    """Get player equipped items"""
    player = get_player()
    return jsonify(player.get_equipped())


@inventory_bp.route('/api/inventory/items', methods=['GET'])
def get_all_items():
    """Get all available items for equipping"""
    player = get_player()
    
    # Get player's inventory items
    inventory_items = InventoryItem.query.filter_by(player_id=player.id).all()
    
    result = []
    for inv_item in inventory_items:
        result.append({
            'inventory_id': inv_item.id,
            'item': inv_item.item.to_dict(),
            'quantity': inv_item.quantity,
            'equipped': any(eq.item_id == inv_item.item_id for eq in player.equipped_items)
        })
    
    return jsonify(result)


@inventory_bp.route('/api/inventory/equip', methods=['POST'])
def equip_item():
    """Equip an item (max 6 slots)"""
    player = get_player()
    
    data = request.json
    item_id = data.get('item_id')
    slot = data.get('slot', len(player.equipped_items))
    
    if slot < 0 or slot > 5:
        return jsonify({'error': 'Slot must be between 0 and 5'}), 400
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Check if player has this item in inventory
    inventory_item = InventoryItem.query.filter_by(
        player_id=player.id,
        item_id=item_id
    ).first()
    
    if not inventory_item:
        return jsonify({'error': 'Item not in inventory'}), 400
    
    # Check if already at max equipped items (now supports 6 slots)
    if len(player.equipped_items) >= 6 and slot >= len(player.equipped_items):
        return jsonify({'error': 'Maximum 6 items can be equipped'}), 400
    
    # Check if slot is already occupied
    existing = EquippedItem.query.filter_by(
        player_id=player.id,
        slot=slot
    ).first()
    
    # Decrement one quantity from the inventory for the equipped item
    # and if replacing an existing equipped item, return it to inventory.
    if existing:
        prev_item_id = existing.item_id
        if prev_item_id != item_id:
            # return previous item to inventory and consume the new one
            adjust_inventory_quantity(player, prev_item_id, 1)
            # set new item in slot
            existing.item_id = item_id
            adjust_inventory_quantity(player, item_id, -1)
    else:
        # consume one of the new item from inventory
        adjust_inventory_quantity(player, item_id, -1)
        # Add new equipped item
        equipped_item = EquippedItem(
            player_id=player.id,
            item_id=item_id,
            slot=slot
        )
        db.session.add(equipped_item)

    db.session.commit()
    return jsonify({
        'message': f'Item {item.name} equipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/unequip/<int:slot>', methods=['DELETE'])
def unequip_item(slot):
    """Unequip an item from a slot"""
    player = get_player()
    
    if slot < 0 or slot > 5:
        return jsonify({'error': 'Slot must be between 0 and 5'}), 400
    
    equipped_item = EquippedItem.query.filter_by(
        player_id=player.id,
        slot=slot
    ).first()
    
    if not equipped_item:
        return jsonify({'error': 'No item in slot'}), 404
    
    # Return the item to the player's inventory (increment or create)
    unequipped_item_id = equipped_item.item_id
    adjust_inventory_quantity(player, unequipped_item_id, 1)

    db.session.delete(equipped_item)
    db.session.commit()

    return jsonify({
        'message': 'Item unequipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['POST'])
def add_item_to_inventory(item_id):
    """Add item to inventory (or increment quantity if already exists)"""
    player = get_player()
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    inventory_item = adjust_inventory_quantity(player, item_id, 1)
    
    db.session.commit()
    return jsonify(inventory_item.to_dict())


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['DELETE'])
def remove_item_from_inventory(item_id):
    """Remove one quantity of item from inventory (or delete if quantity becomes 0)"""
    player = get_player()
    inventory_item = adjust_inventory_quantity(player, item_id, -1)
    
    if not inventory_item:
        return jsonify({'error': 'Item not in inventory'}), 404
    
    db.session.commit()
    return jsonify({'message': 'Item removed from inventory'})


@inventory_bp.route('/api/inventory/clear', methods=['DELETE'])
def clear_inventory():
    """Clear all items from player inventory"""
    player = get_player()
    clear_player_inventory(player)
    db.session.commit()
    
    return jsonify({'message': 'Inventory cleared'})


@inventory_bp.route('/api/inventory/reforge_all', methods=['POST'])
def reforge_all_items():
    """Server-side loop: repeatedly reforge any items with quantity >= 3 until none remain."""
    player = get_player()

    made_changes = False
    while True:
        inv_item = InventoryItem.query.filter_by(player_id=player.id).filter(InventoryItem.quantity >= 3).first()
        if not inv_item:
            break

        made_changes = True
        item = Item.query.get(inv_item.item_id)
        if not item:
            db.session.delete(inv_item)
            db.session.commit()
            continue

        adjust_inventory_quantity(player, inv_item.item_id, -3)
        upgraded = get_upgraded_item(item)
        adjust_inventory_quantity(player, upgraded.id, 1)
        db.session.commit()

    if not made_changes:
        return jsonify({'message': 'No items to reforge'}), 400

    return jsonify({'message': 'Reforge all complete', 'player': player.to_dict(include_inventory=True)})
