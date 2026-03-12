from flask import Blueprint, jsonify, request
from database import db
from models import Player

player_bp = Blueprint('player', __name__)


@player_bp.route('/api/player', methods=['GET'])
def get_player():
    """Get player stats"""
    player = Player.query.first()
    if not player:
        player = Player(health=100, damage=10, level=1)
        db.session.add(player)
        db.session.commit()
    return jsonify(player.to_dict())


@player_bp.route('/api/player', methods=['PUT'])
def update_player():
    """Update player stats"""
    data = request.json
    player = Player.query.first()

    if not player:
        player = Player()
        db.session.add(player)

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

    if not player:
        player = Player()
        db.session.add(player)

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
    if not player:
        player = Player()
        db.session.add(player)

    player.health = max(0, player.health - damage_amount)
    db.session.commit()

    return jsonify(player.to_dict())
