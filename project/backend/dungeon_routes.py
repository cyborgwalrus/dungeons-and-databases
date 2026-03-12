import random
from flask import Blueprint, jsonify
from database import db
from models import Player, EnemyType, CurrentEncounter

dungeon_bp = Blueprint('dungeon', __name__)


def create_new_encounter():
    """Create a new enemy encounter"""
    player = Player.query.first()
    if not player:
        player = Player(health=100, damage=10, level=1)
        db.session.add(player)
        db.session.commit()

    # Clear any existing encounter
    CurrentEncounter.query.delete()

    # Select random enemy type
    enemy_type = EnemyType.query.order_by(db.func.random()).first()

    # Scale enemy stats based on player level
    max_health = enemy_type.base_health + (player.level * 10)
    damage = enemy_type.base_damage + (player.level * 2)

    encounter = CurrentEncounter(
        enemy_type_id=enemy_type.id,
        current_health=max_health,
        max_health=max_health,
        damage=damage
    )
    db.session.add(encounter)
    db.session.commit()

    return encounter


def check_player_death(player):
    """Check if player is dead and reset if necessary. Returns True if player died."""
    if player.health <= 0:
        player.health = 100
        player.damage = 10
        player.level = 1

        # Clear any active encounter
        CurrentEncounter.query.delete()

        return True
    return False


@dungeon_bp.route('/api/dungeon/encounter', methods=['GET'])
def get_encounter():
    """Get or create current enemy encounter"""
    encounter = CurrentEncounter.query.first()

    if not encounter:
        encounter = create_new_encounter()

    return jsonify(encounter.to_dict())


@dungeon_bp.route('/api/dungeon/attack', methods=['POST'])
def attack_monster():
    """Attack a monster in the dungeon"""
    player = Player.query.first()
    if not player:
        player = Player()
        db.session.add(player)

    encounter = CurrentEncounter.query.first()
    if not encounter:
        encounter = create_new_encounter()

    # Combat simulation
    player_hits = random.randint(player.damage // 2, player.damage)
    monster_hits = random.randint(encounter.damage // 2, encounter.damage)

    # Apply damage to enemy
    encounter.current_health = max(0, encounter.current_health - player_hits)

    # Player takes damage from monster if it's still alive
    if encounter.current_health > 0:
        player.health = max(0, player.health - monster_hits)

        # Check if player died
        player_died = check_player_death(player)

        if player_died:
            message = f"{encounter.enemy_type.name} dealt {monster_hits} damage to you! You have been defeated and returned to the start..."
            db.session.commit()
            return jsonify({
                'player': player.to_dict(),
                'enemy': None,
                'message': message,
                'victory': False,
                'player_died': True
            })

        message = (
            f"You dealt {player_hits} damage to {encounter.enemy_type.name}! "
            f"It has {encounter.current_health} HP left. "
            f"{encounter.enemy_type.name} dealt {monster_hits} damage to you!"
        )
        victory = False
    else:
        # Enemy defeated
        message = f"Victory! You dealt {player_hits} damage and defeated the {encounter.enemy_type.name}!"
        victory = True

        # Reward: chance to level up and gain stats
        if random.random() < 0.4:  # 40% chance
            player.level += 1
            player.damage += 3
            player.health = min(player.health + 20, 100 + (player.level * 10))
            message += " You leveled up!"

        # Create new encounter for next battle
        db.session.delete(encounter)
        encounter = create_new_encounter()

    db.session.commit()

    return jsonify({
        'player': player.to_dict(),
        'enemy': encounter.to_dict(),
        'message': message,
        'victory': victory,
        'player_died': False
    })


@dungeon_bp.route('/api/dungeon/run', methods=['POST'])
def run_away():
    """Attempt to run away from the dungeon"""
    player = Player.query.first()
    if not player:
        player = Player()
        db.session.add(player)

    encounter = CurrentEncounter.query.first()
    if not encounter:
        encounter = create_new_encounter()

    # Roll a dice (1-6)
    dice_roll = random.randint(1, 6)

    # Need to roll 5 or 6 to escape
    if dice_roll >= 5:
        message = f"You rolled a {dice_roll}! You successfully escaped and returned home!"
        damage_taken = 0

        # Clear encounter - player escaped back home
        db.session.delete(encounter)
        db.session.commit()
    
        return jsonify({
            'player': player.to_dict(),
            'enemy': None,
            'message': message,
            'damage': damage_taken,
            'dice_roll': dice_roll,
            'success': True,
            'player_died': False
        })
    else:
        # Failed to escape - enemy attacks you
        damage_taken = random.randint(encounter.damage // 2, encounter.damage)
        player.health = max(0, player.health - damage_taken)
        message = (
            f"You rolled a {dice_roll}! Failed to escape! "
            f"{encounter.enemy_type.name} caught you and dealt {damage_taken} damage!"
        )

        # Check if player died while trying to run
        player_died = check_player_death(player)

        if player_died:
            message = (
                f"You rolled a {dice_roll} and failed to escape. "
                f"{encounter.enemy_type.name} dealt {damage_taken} damage! "
                f"You have been defeated and returned to the start..."
            )
            db.session.commit()
            return jsonify({
                'player': player.to_dict(),
                'enemy': None,
                'message': message,
                'damage': damage_taken,
                'dice_roll': dice_roll,
                'success': False,
                'player_died': True
            })

    db.session.commit()

    return jsonify({
        'player': player.to_dict(),
        'enemy': encounter.to_dict(),
        'message': message,
        'damage': damage_taken,
        'dice_roll': dice_roll,
        'success': False,
        'player_died': False
    })
