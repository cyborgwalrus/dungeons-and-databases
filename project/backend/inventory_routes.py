from flask import Blueprint, jsonify, request
from models import db, Item, ItemType
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
    all_items = Item.query.filter_by(owner_id=player.id).all()
    return jsonify([
        {
            'inventory_id': item.id,
            'item': item.to_dict(),
            'equipped': item.is_equipped,
            'slot': item.slot,
        }
        for item in all_items
    ])


@inventory_bp.route('/api/inventory/equip', methods=['POST'])
def equip_item():
    """Equip an item (max 6 slots)"""
    player = get_player()
    
    data = request.json or {}
    item_id = data.get('item_id')
    slot = int(data.get('slot', len(player.equipped_items)))
    source_slot = data.get('source_slot')
    source_slot = int(source_slot) if source_slot is not None else None
    
    if slot < 0 or slot > 5:
        return jsonify({'error': 'Slot must be between 0 and 5'}), 400
    
    item = Item.query.filter_by(owner_id=player.id, id=item_id).first()
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    source_equipped = Item.query.filter_by(owner_id=player.id, id=item_id, is_equipped=True).first()

    if source_equipped:
        existing = Item.query.filter_by(owner_id=player.id, is_equipped=True, slot=slot).first()

        if existing and existing.id != source_equipped.id:
            existing.slot = source_equipped.slot

        source_equipped.slot = slot
        db.session.commit()
        db.session.expire(player)
        return jsonify({
            'message': f'Item {item.item_type.name if item.item_type else item.id} equipped',
            'player': player.to_dict(include_inventory=True)
        })

    inventory_item = Item.query.filter_by(owner_id=player.id, id=item_id, is_equipped=False).first()
    if not inventory_item:
        return jsonify({'error': 'Item not in inventory'}), 400

    existing = Item.query.filter_by(owner_id=player.id, is_equipped=True, slot=slot).first()
    if existing:
        existing.slot = None
        existing.is_equipped = False

    inventory_item.is_equipped = True
    inventory_item.slot = slot

    db.session.commit()
    db.session.expire(player)
    return jsonify({
        'message': f'Item {inventory_item.item_type.name if inventory_item.item_type else inventory_item.id} equipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/unequip/<int:slot>', methods=['DELETE'])
def unequip_item(slot):
    """Unequip an item from a slot"""
    player = get_player()
    
    if slot < 0 or slot > 5:
        return jsonify({'error': 'Slot must be between 0 and 5'}), 400
    
    equipped_item = Item.query.filter_by(owner_id=player.id, is_equipped=True, slot=slot).first()
    
    if not equipped_item:
        return jsonify({'error': 'No item in slot'}), 404
    
    equipped_item.is_equipped = False
    equipped_item.slot = None
    db.session.commit()
    db.session.expire(player)

    return jsonify({
        'message': 'Item unequipped',
        'player': player.to_dict(include_inventory=True)
    })


@inventory_bp.route('/api/inventory/item/<int:item_id>', methods=['POST'])
def add_item_to_inventory(item_id):
    """Add item to inventory."""
    player = get_player()
    
    item_type = ItemType.query.get(item_id)
    if not item_type:
        return jsonify({'error': 'Item not found'}), 404
    
    inventory_item = add_inventory_item(player, item_type.id)
    
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
        inventory_items = Item.query.filter_by(owner_id=player.id, is_equipped=False).all()
        equipped_items = Item.query.filter_by(owner_id=player.id, is_equipped=True).all()
        if not inventory_items and not equipped_items:
            break

        groups = {}
        for inv_item in inventory_items:
            groups.setdefault(inv_item.item_type_id, []).append({'kind': 'inventory', 'row': inv_item})
        for eq_item in equipped_items:
            groups.setdefault(eq_item.item_type_id, []).append({'kind': 'equipped', 'row': eq_item})

        upgrade_source = next((group[0] for group in groups.values() if len(group) >= 3), None)
        if not upgrade_source:
            break

        made_changes = True
        items_to_consume = groups[upgrade_source['row'].item_type_id][:3]
        source_row = next((entry['row'] for entry in items_to_consume if entry['kind'] == 'equipped'), None)

        for entry in items_to_consume:
            if entry['row'] is not source_row:
                db.session.delete(entry['row'])

        upgraded = get_upgraded_item(upgrade_source['row'])
        if source_row:
            source_row.item_type_id = upgraded.item_type_id
            source_row.level = upgraded.level
            source_row.is_loot = upgraded.is_loot
            db.session.delete(upgraded)
        else:
            new_item = add_inventory_item(player, upgraded.item_type_id)
            new_item.level = upgraded.level
            new_item.is_loot = upgraded.is_loot
            db.session.delete(upgraded)

        db.session.commit()

    if not made_changes:
        return jsonify({'message': 'No items to reforge'}), 400

    db.session.expire(player)
    return jsonify({'message': 'Reforge all complete', 'player': player.to_dict(include_inventory=True)})


@inventory_bp.route('/api/inventory/equip-best', methods=['POST'])
def equip_best_items():
    """Equip the best matching items into each slot."""
    player = get_player()
    slot_defs = ['helmet', 'armor', 'weapon', 'shield', 'ring', 'necklace']

    for slot_index, slot_type in enumerate(slot_defs):
        candidates = [
            item for item in Item.query.filter_by(owner_id=player.id, is_equipped=False).all()
            if item.item_type and _item_type_matches_slot(item.item_type, slot_type)
        ]
        if not candidates:
            continue

        best_item = max(candidates, key=lambda item: _item_score(item.item_type, slot_type))
        best_item.is_equipped = True

    db.session.commit()
    db.session.expire(player)
    return jsonify({'message': 'Best items equipped', 'player': player.to_dict(include_inventory=True)})


def _item_type_matches_slot(item_type, slot_type):
    name = (item_type.name or '').lower()
    if slot_type == 'shield':
        return 'shield' in name
    if slot_type == 'helmet':
        return 'helmet' in name or 'helm' in name or 'cap' in name
    if slot_type == 'necklace':
        return 'necklace' in name or 'amulet' in name
    if slot_type == 'ring':
        return 'ring' in name
    if slot_type == 'weapon':
        return item_type.bonus_attack > 0 and item_type.bonus_health == 0
    if slot_type == 'armor':
        return item_type.bonus_health > 0 and item_type.bonus_attack == 0
    return True


def _item_score(item_type, slot_type):
    attack = item_type.bonus_attack or 0
    health = item_type.bonus_health or 0
    if slot_type == 'weapon':
        return attack * 10 + health
    return health * 10 + attack


