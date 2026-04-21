# Database

## Database Design and Implementation

![alt text](docs/database-schema.png)

## Database Schema

### File Organization

- **models.py**: SQLAlchemy ORM model definitions for all entities with table relationships and helper methods
- **init_db.py**: Database initialization, schema creation via `db.create_all()`, and seed data loading
- **cache_helpers.py**: Memoized queries for reference data (ItemType, EnemyType) to reduce database hits

### Data Reset in development mode

If the Flask app is running in development mode using `FLASK_ENV=development`, the database is automatically wiped and reseeded on every application restart. This allows for rapid iteration without manual cleanup. In production mode, the database persists across restarts. To manually reset the database in any environment, use the following Flask CLI commands:

```bash
# Create tables and load seed data
flask init-db

# Drop all tables and remove the database file
flask delete-db
```

### Schema Details

### User

The User table represents a player account. Each user has a unique username and password used for authentication. Users receive an API token upon signup/signin for subsequent authenticated requests. Each user can own multiple characters and one shared inventory.


User | Type | Description | Relations
-- | -- | -- | --
id | int | User ID | PK
username | string | Username | unique
password | string | Hashed password | -

### UserInventory

Each user owns exactly one inventory. This inventory stores unequipped items that can be shared across all of the user's characters. Items move between the user's shared inventory and character equipment via equip/unequip operations.

UserInventory | Type | Description | Relations
-- | -- | -- | --
id | int | Inventory ID | PK
user_id | int | Owning user | FK User.id (unique)
items | relationship | Items in this inventory | Item.inventory_id -> UserInventory.id

### Character

The Character table represents a playable character. Each character:
- Belongs to a single user
- Has basic attributes: name, level, health, damage, experience
- Levels up when experience reaches the threshold (consuming that experience)
- Can have items equipped in specific equipment slots
- Participates in dungeon encounters

Character | Type | Description | Relations
-- | -- | -- | --
id | int | Character ID | PK
user_id | int | Owning User's id | FK User.id
name | string | Character name | -
level | int | Current level (increases with experience) | -
experience | int | Current experience points | -
health | int | Current health | -
damage | int | Base damage (before equipment bonuses) | -
max_health | property | Max health based on level + equipped bonuses | calculated
bonus_damage | property | Total damage from equipped items | calculated

### ItemType

The ItemType table defines item templates with static attributes like name, equipment slot, and base health/damage values. ItemType templates are cached in memory and used as blueprints when items are looted or created.

ItemType | Type | Description | Relations
-- | -- | -- | --
id | int | Item type ID | PK
name | string | Item name | -
slot | enum | Equipment slot: weapon, shield, armor, helmet, ring, necklace | -
health | int | Base health bonus | -
damage | int | Base damage bonus | -
description | string | Item description | -

### Item

Each Item row represents an actual item instance owned by a player. Items are created from ItemType templates and include:
- An item level that scales the base health/damage from the template
- An `is_loot` flag indicating whether the item was dropped during the current dungeon run
- A reference to the owning UserInventory (when not equipped)

When a character is defeated during a dungeon run, all items with `is_loot=true` are deleted. Successfully looted items are permanently added to the user's inventory.


Item | Type | Description | Relations
-- | -- | -- | --
id | int | Item ID | PK
name | string | Item name (from ItemType) | -
level | int | Item level (scales damage/health from base) | -
health | int | Effective health (base + level scaling) | -
damage | int | Effective damage (base + level scaling) | -
item_type_id | int | Reference item template | FK ItemType.id
inventory_id | int | Owning user's inventory (null if equipped) | FK UserInventory.id (nullable)
is_loot | boolean | Marked as loot from current dungeon run | -

### CharacterEquipment

CharacterEquipment links an item to a character's equipment slot. Each character can equip one item per slot (weapon, armor, shield, helmet, ring, necklace). Equipping moves an item out of the shared inventory into this table; unequipping reverses the process.

CharacterEquipment | Type | Description | Relations
-- | -- | -- | --
id | int | Equipment row ID | PK
character_id | int | Equipped character | FK Character.id
item_id | int | Equipped item | FK Item.id (unique)
slot | enum | Equipment slot | validates ItemType.slot

### Encounter

An Encounter represents an active dungeon combat scenario. When a player enters the dungeon:
1. An Encounter is created and linked to the character
2. An EnemyType is randomly selected and its stats are scaled to the current `enemy_level`
3. Health and damage values are stored in the Encounter row
4. After victory, a new Encounter is created at a higher `enemy_level` based on character progression
5. Defeating an enemy grants experience based on `enemy_level`, not the base EnemyType

The enemy_level increases with each victory, scaled by the character's level for difficulty progression.

Encounter | Type | Description | Relations
-- | -- | -- | --
id | int | Encounter ID | PK
character_id | int | Player character | FK Character.id (unique)
enemy_type_id | int | Enemy template | FK EnemyType.id
enemy_level | int | Scaled difficulty level | -
max_health | int | Enemy max health (base + level scaling) | -
health | int | Current enemy health | -
damage | int | Enemy damage (base + level scaling) | -

### EnemyType

EnemyType defines monster templates with static base attributes. Each EnemyType is cached at startup and reused across multiple encounters with scaling applied per encounter.


EnemyType | Type | Description | Relations
-- | -- | -- | --
id | int | Enemy type ID | PK
name | string | Enemy name | -
health | int | Base health value | -
damage | int | Base damage value | -
description | string | Enemy description | -

---

### Item Stacking and Level

Items don't merge or stack—each Item object is independent. Item level scales damage/health linearly from the base ItemType values. The formula applied during item creation:

```
effective_value = base_value + (item_level - 1) * base_value * 0.25
```

### Relationships

Key relationships to understand:

- **User ↔ Character**: One-to-many. Deleting a user cascades to all characters.
- **User ↔ UserInventory**: One-to-one. Each user has exactly one shared inventory.
- **UserInventory ↔ Item**: One-to-many. Items belong to a user's inventory until equipped.
- **Character ↔ CharacterEquipment**: One-to-many. Equipment rows link items to character slots.
- **Character ↔ Encounter**: One-to-many. A character can have zero or one active encounter; old encounters are deleted when new ones are created.
- **ItemType ↔ Item**: One-to-many. Templates are cached; items reference them via item_type_id.
- **EnemyType ↔ Encounter**: One-to-many. Encounters reference templates for serialization.

### Cascade Behavior

Deletions cascade automatically:

- Deleting a User deletes all related Characters, UserInventory, CharacterEquipment, and Encounters
- Deleting a Character deletes its CharacterEquipment and Encounters
- Deleting a UserInventory deletes all Items in that inventory
- 
