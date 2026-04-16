from flask import Blueprint, jsonify, request
from models import db, ItemType
from game_utils import add_inventory_item, get_player as get_current_player

player_bp = Blueprint('player', __name__)


@player_bp.route('/api/player', methods=['GET'])
def get_player():
    """Get player stats"""
    player = get_current_player()
    return jsonify(player.to_dict())


@player_bp.route('/api/player', methods=['PUT'])
def update_player():
    """Update player stats"""
    data = request.json
    player = get_current_player()

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
    player = get_current_player()

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

    player = get_current_player()
    player.health = max(0, player.health - damage_amount)
    db.session.commit()

    return jsonify(player.to_dict())


@player_bp.route('/api/player/full', methods=['GET'])
def get_player_with_inventory():
    """Get player stats including inventory"""
    player = get_current_player()
    return jsonify(player.to_dict(include_inventory=True))


@player_bp.route('/api/demo/inventory', methods=['POST'])
def demo_inventory():
    """Demo endpoint to add random items to player inventory"""
    player = get_current_player()
    
    # Get some random item types
    items = ItemType.query.limit(3).all()
    
    for item in items:
        add_inventory_item(player, item.id)
    
    db.session.commit()
    return jsonify({
        'message': 'Added demo items to inventory',
        'player': player.to_dict(include_inventory=True)
    })
