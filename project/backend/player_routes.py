from flask import Blueprint, jsonify, request
from database import db
from models import Player, Item, InventoryItem

player_bp = Blueprint('player', __name__)


@player_bp.route('/api/player', methods=['GET'])
def get_player():
    """Get player stats"""
    player = Player.query.first()
    return jsonify(player.to_dict())


@player_bp.route('/api/player', methods=['PUT'])
def update_player():
    """Update player stats"""
    data = request.json
    player = Player.query.first()

    if 'health' in data:
        player.health = data['health']
    if 'damage' in data:
        player.damage = data['damage']
    if 'level' in data:
        player.level = data['level']

    db.session.commit()
    return jsonify(player.to_dict())


@player_bp.route('/api/player/level-up', methods=['POST'])
def level_up():
    """Increase player level and stats"""
    player = Player.query.first()

    player.level += 1
    player.damage += 5
    player.health += 10

    db.session.commit()
    return jsonify(player.to_dict())


@player_bp.route('/api/health', methods=['POST'])
def take_damage():
    """Player takes damage"""
    data = request.json
    damage_amount = data.get('damage', 0)

    player = Player.query.first()
    player.health = max(0, player.health - damage_amount)
    db.session.commit()

    return jsonify(player.to_dict())


@player_bp.route('/api/player/full', methods=['GET'])
def get_player_with_inventory():
    """Get player stats including inventory"""
    player = Player.query.first()
    return jsonify(player.to_dict(include_inventory=True))


@player_bp.route('/api/demo/inventory', methods=['POST'])
def demo_inventory():
    """Demo endpoint to add random items to player inventory"""
    player = Player.query.first()
    
    # Get some random items
    items = Item.query.limit(3).all()
    
    for item in items:
        # Check if player already has this item
        inventory_item = InventoryItem.query.filter_by(
            player_id=player.id,
            item_id=item.id
        ).first()
        
        if inventory_item:
            inventory_item.quantity += 1
        else:
            inventory_item = InventoryItem(
                player_id=player.id,
                item_id=item.id,
                quantity=1
            )
            db.session.add(inventory_item)
    
    db.session.commit()
    return jsonify({
        'message': 'Added demo items to inventory',
        'player': player.to_dict(include_inventory=True)
    })
