from flask import Blueprint, jsonify, request
from database import db
from models import Player, Item, InventoryItem, EquippedItem

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get player inventory"""
    player = Player.query.first()
    return jsonify(player.get_inventory())


@inventory_bp.route('/api/inventory/equipped', methods=['GET'])
def get_equipped():
    """Get player equipped items"""
    player = Player.query.first()
    return jsonify(player.get_equipped())


@inventory_bp.route('/api/inventory/items', methods=['GET'])
def get_all_items():
    """Get all available items for equipping"""
    player = Player.query.first()
    
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
    """Equip an item (max 5 slots)"""
    player = Player.query.first()
    
    data = request.json
    item_id = data.get('item_id')
    slot = data.get('slot', len(player.equipped_items))
    
    if slot < 0 or slot > 4:
        return jsonify({'error': 'Slot must be between 0 and 4'}), 400
    
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
    
    # Check if already at max equipped items
    if len(player.equipped_items) >= 5 and slot >= len(player.equipped_items):
        return jsonify({'error': 'Maximum 5 items can be equipped'}), 400
    
    # Check if slot is already occupied
    existing = EquippedItem.query.filter_by(
        player_id=player.id,
        slot=slot
    ).first()
    
    if existing:
        # Replace the item in this slot
        existing.item_id = item_id
    else:
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
    player = Player.query.first()
    
    if slot < 0 or slot > 4:
        return jsonify({'error': 'Slot must be between 0 and 4'}), 400
    
    equipped_item = EquippedItem.query.filter_by(
        player_id=player.id,
        slot=slot
    ).first()
    
    if not equipped_item:
        return jsonify({'error': 'No item in slot'}), 404
    
    db.session.delete(equipped_item)
    db.session.commit()
    
    return jsonify({
        'message': 'Item unequipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['POST'])
def add_item_to_inventory(item_id):
    """Add item to inventory (or increment quantity if already exists)"""
    player = Player.query.first()
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Check if player already has this item
    inventory_item = InventoryItem.query.filter_by(
        player_id=player.id,
        item_id=item_id
    ).first()
    
    if inventory_item:
        # Increase quantity
        inventory_item.quantity += 1
    else:
        # Add new item
        inventory_item = InventoryItem(
            player_id=player.id,
            item_id=item_id,
            quantity=1
        )
        db.session.add(inventory_item)
    
    db.session.commit()
    return jsonify(inventory_item.to_dict())


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['DELETE'])
def remove_item_from_inventory(item_id):
    """Remove one quantity of item from inventory (or delete if quantity becomes 0)"""
    player = Player.query.first()
    
    inventory_item = InventoryItem.query.filter_by(
        player_id=player.id,
        item_id=item_id
    ).first()
    
    if not inventory_item:
        return jsonify({'error': 'Item not in inventory'}), 404
    
    if inventory_item.quantity > 1:
        inventory_item.quantity -= 1
    else:
        db.session.delete(inventory_item)
    
    db.session.commit()
    return jsonify({'message': 'Item removed from inventory'})


@inventory_bp.route('/api/inventory/clear', methods=['DELETE'])
def clear_inventory():
    """Clear all items from player inventory"""
    player = Player.query.first()
    
    InventoryItem.query.filter_by(player_id=player.id).delete()
    db.session.commit()
    
    return jsonify({'message': 'Inventory cleared'})
