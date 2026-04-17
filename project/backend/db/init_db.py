import csv
import os

from .models import EnemyType, ItemType, db


def _load_csv_rows(filename):
    csv_path = os.path.join(os.path.dirname(__file__), filename)
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))


ENEMY_TYPES = [
    {
        'name': row['name'],
        'base_health': int(row['base_health']),
        'base_damage': int(row['base_damage']),
        'description': row['description'],
    }
    for row in _load_csv_rows('enemy_types.csv')
]

ITEM_TYPES = [
    {
        'name': row['name'],
        'slot': row['slot'],
        'base_health_bonus': int(row['base_health_bonus']),
        'base_damage_bonus': int(row['base_damage_bonus']),
    }
    for row in _load_csv_rows('item_types.csv')
]


def seed_initial_data():
    if EnemyType.query.count() == 0:
        db.session.add_all([EnemyType(**seed) for seed in ENEMY_TYPES])
        db.session.commit()

    if ItemType.query.count() == 0:
        db.session.add_all([ItemType(**seed) for seed in ITEM_TYPES])
        db.session.commit()