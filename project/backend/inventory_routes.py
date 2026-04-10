from flask import Blueprint, jsonify, request
from database import db
from models import Item, InventoryItem, EquippedItem
from game_utils import add_inventory_item, clear_player_inventory, get_player, get_upgraded_item, remove_inventory_item

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
    
    if existing:
        prev_item_id = existing.item_id
        if prev_item_id != item_id:
            add_inventory_item(player, prev_item_id)
            existing.item_id = item_id
            remove_inventory_item(player, item_id)
    else:
        remove_inventory_item(player, item_id)
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
    
    unequipped_item_id = equipped_item.item_id
    add_inventory_item(player, unequipped_item_id)

    db.session.delete(equipped_item)
    db.session.commit()

    return jsonify({
        'message': 'Item unequipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['POST'])
def add_item_to_inventory(item_id):
    """Add item to inventory."""
    player = get_player()
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    inventory_item = add_inventory_item(player, item_id)
    
    db.session.commit()
    return jsonify(inventory_item.to_dict())


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['DELETE'])
def remove_item_from_inventory(item_id):
    """Remove one item from inventory."""
    player = get_player()
    inventory_item = remove_inventory_item(player, item_id)
    
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
    """Reforge every set of 3 matching items into one upgraded copy."""
    player = get_player()
    made_changes = False

    while True:
        inventory_items = InventoryItem.query.filter_by(player_id=player.id).all()
        equipped_items = EquippedItem.query.filter_by(player_id=player.id).all()
        if not inventory_items and not equipped_items:
            break

        groups = {}
        for inv_item in inventory_items:
            groups.setdefault(inv_item.item_id, []).append({'kind': 'inventory', 'row': inv_item})
        for eq_item in equipped_items:
            groups.setdefault(eq_item.item_id, []).append({'kind': 'equipped', 'row': eq_item})

        upgrade_source = next((group[0] for group in groups.values() if len(group) >= 3), None)
        if not upgrade_source:
            break

        made_changes = True
        items_to_consume = groups[upgrade_source['row'].item_id][:3]
        source_row = next((entry['row'] for entry in items_to_consume if entry['kind'] == 'equipped'), None)

        for entry in items_to_consume:
            if entry['kind'] == 'equipped':
                if entry['row'] is not source_row:
                    db.session.delete(entry['row'])
            else:
                db.session.delete(entry['row'])

        upgraded = get_upgraded_item(upgrade_source['row'].item)
        if source_row:
            source_row.item_id = upgraded.id
        else:
            add_inventory_item(player, upgraded.id)

        db.session.commit()

    if not made_changes:
        return jsonify({'message': 'No items to reforge'}), 400

    return jsonify({'message': 'Reforge all complete', 'player': player.to_dict(include_inventory=True)})


