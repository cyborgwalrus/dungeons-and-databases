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
    """Equip an item (max 6 slots)"""
    player = Player.query.first()
    
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
            # return previous item to inventory (increment or create)
            prev_inv = InventoryItem.query.filter_by(player_id=player.id, item_id=prev_item_id).first()
            if prev_inv:
                prev_inv.quantity += 1
            else:
                prev_inv = InventoryItem(player_id=player.id, item_id=prev_item_id, quantity=1)
                db.session.add(prev_inv)
            # set new item in slot
            existing.item_id = item_id
            # consume one of the new item from inventory
            if inventory_item.quantity > 1:
                inventory_item.quantity -= 1
            else:
                db.session.delete(inventory_item)
    else:
        # consume one of the new item from inventory
        if inventory_item.quantity > 1:
            inventory_item.quantity -= 1
        else:
            db.session.delete(inventory_item)
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
    inv = InventoryItem.query.filter_by(player_id=player.id, item_id=unequipped_item_id).first()
    if inv:
        inv.quantity += 1
    else:
        inv = InventoryItem(player_id=player.id, item_id=unequipped_item_id, quantity=1)
        db.session.add(inv)

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


@inventory_bp.route('/api/inventory/reforge', methods=['POST'])
def reforge_item():
    """Combine three of the same item into a +1 upgraded version with doubled stats"""
    data = request.json or {}
    item_id = data.get('item_id')
    player = Player.query.first()

    if not item_id:
        return jsonify({'error': 'item_id required'}), 400

    inventory_item = InventoryItem.query.filter_by(player_id=player.id, item_id=item_id).first()
    if not inventory_item or inventory_item.quantity < 3:
        return jsonify({'error': 'Need at least 3 of the same item to reforge'}), 400

    base_item = Item.query.get(item_id)
    if not base_item:
        return jsonify({'error': 'Base item not found'}), 404

    # consume three of the base item
    if inventory_item.quantity > 3:
        inventory_item.quantity -= 3
    else:
        # quantity == 3 -> remove record
        db.session.delete(inventory_item)

    # determine existing +N suffix so we can increment levels
    import re
    m = re.search(r"\s\+(\d+)$", base_item.name)
    if m:
        try:
            curr_level = int(m.group(1))
        except Exception:
            curr_level = 0
        base_name = base_item.name[:m.start()].strip()
    else:
        curr_level = 0
        base_name = base_item.name

    new_level = curr_level + 1

    # create or reuse upgraded item (+new_level) with doubled stats from the consumed item
    upgraded_name = f"{base_name} +{new_level}"
    existing_upgraded = Item.query.filter_by(name=upgraded_name).first()
    if existing_upgraded:
        upgraded = existing_upgraded
    else:
        upgraded = Item(
            name=upgraded_name,
            description=(base_item.description or '') + f' (Reforged +{new_level})',
            bonus_attack=(base_item.bonus_attack or 0) * 2,
            bonus_health=(base_item.bonus_health or 0) * 2
        )
        db.session.add(upgraded)
        db.session.commit()  # commit to get upgraded.id

    # give player the upgraded item (increment if already present)
    new_inv = InventoryItem.query.filter_by(player_id=player.id, item_id=upgraded.id).first()
    if new_inv:
        new_inv.quantity += 1
    else:
        new_inv = InventoryItem(player_id=player.id, item_id=upgraded.id, quantity=1)
        db.session.add(new_inv)
    db.session.commit()

    return jsonify({'message': 'Reforge complete', 'upgraded_item': upgraded.to_dict(), 'player': player.to_dict(include_inventory=True)})


@inventory_bp.route('/api/inventory/reforge_all', methods=['POST'])
def reforge_all_items():
    """Server-side loop: repeatedly reforge any items with quantity >= 3 until none remain."""
    player = Player.query.first()

    made_changes = False
    # loop until no candidate
    while True:
        inv_item = InventoryItem.query.filter(InventoryItem.player_id == player.id, InventoryItem.quantity >= 3).first()
        if not inv_item:
            break
        made_changes = True
        item = Item.query.get(inv_item.item_id)
        if not item:
            # should not happen, skip
            # remove this inventory record to avoid infinite loop
            db.session.delete(inv_item)
            db.session.commit()
            continue

        # consume three
        if inv_item.quantity > 3:
            inv_item.quantity -= 3
        else:
            db.session.delete(inv_item)

        # determine level and base name
        import re
        m = re.search(r"\s\+(\d+)$", item.name)
        if m:
            try:
                curr_level = int(m.group(1))
            except Exception:
                curr_level = 0
            base_name = item.name[:m.start()].strip()
        else:
            curr_level = 0
            base_name = item.name

        new_level = curr_level + 1
        upgraded_name = f"{base_name} +{new_level}"

        existing_upgraded = Item.query.filter_by(name=upgraded_name).first()
        if existing_upgraded:
            upgraded = existing_upgraded
        else:
            upgraded = Item(
                name=upgraded_name,
                description=(item.description or '') + f' (Reforged +{new_level})',
                bonus_attack=(item.bonus_attack or 0) * 2,
                bonus_health=(item.bonus_health or 0) * 2
            )
            db.session.add(upgraded)
            db.session.commit()

        # give upgraded item to player
        new_inv = InventoryItem.query.filter_by(player_id=player.id, item_id=upgraded.id).first()
        if new_inv:
            new_inv.quantity += 1
        else:
            new_inv = InventoryItem(player_id=player.id, item_id=upgraded.id, quantity=1)
            db.session.add(new_inv)

        db.session.commit()

    if not made_changes:
        return jsonify({'message': 'No items to reforge'}), 400

    return jsonify({'message': 'Reforge all complete', 'player': player.to_dict(include_inventory=True)})
