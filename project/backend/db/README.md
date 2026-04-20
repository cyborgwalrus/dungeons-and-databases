# Database

## Overview

The game backend's database consists of following entities: User, Character, Item, ItemType, EnemyType and Encounter.

The relationships between tables were defined using foreign keys in the database schema, and are extended with SQLAlchemy relationships to populate related objects in JSON responses.

## Database design and implementation

![alt text](docs/database-schema.png)

## Database design

### User

The User table represents a player account. Each user has a unique username, a password and can own multiple characters. Username and password will be used to login and obtain an API token for authenticating with the APIs endpoints.

### UserInventory

Each user owns exactly one inventory row. This inventory stores unequipped items that can be shared across characters on the same account.

### Character

The Character table represents a playable character. Each character belongs to a user and contains basic attributes such as level, experience, health, and damage. Equipped items are stored separately from the shared user inventory. One item of each type can be equipped to increase the character's stats.

### ItemType

The ItemType table defines item templates that store static item attributes.
When the player receives loot in a dungeon, an ItemType template is instantiated into an Item object with item-level health and damage values.

### Item

A table of items that players have looted from the dungeon. Each Item is connected to one ItemType template and one shared UserInventory row. The player can combine multiple items together to create a new item with a higher item level that will be used in damage calculations. When an item is dropped in the dungeon, it starts with its is_loot flag set to true. If the player is defeated during a dungeon run, all items marked with is_loot are deleted from their inventory.

### CharacterEquipment

A table of equipped items for a character. Each row links one item to one character and one equipment slot. Equipping moves the item out of the shared inventory and into this table; unequipping moves it back.

### Encounter

When the player enters a dungeon, an Encounter entry is created and connected to the player character using a foreign key. An EnemyType is chosen at random to face the player character, and the EnemyType entry's health and damage values are scaled to the active dungeon enemy level and stored in the Encounter's health and damage fields. Defeating enemies awards experience based on the active enemy level, and each new monster in the same dungeon run starts one or more levels higher depending on the character's level.

### EnemyType

A table holding monster templates. Each EnemyType entry has an id, name, description, base_health and base_damage.

---

User | Type | Description | Relations
-- | -- | -- | --
id | int | User ID | PK
username | string | Username | unique
password | string | Password | -

Character | Type | Description | Relations
-- | -- | -- | --
id | int | Character ID | PK
user_id | int | Owning User's id | FK User.id
name | string | Name | -
level | int | Level | -
health | int | Health | -
damage | int | Damage | -
equipment | list | Equipped item rows | CharacterEquipment.character_id -> Character.id

ItemType | Type | Description | Relations
-- | -- | -- | --
id | int | Item type ID | PK
name | string | Item name | -
slot | enum | Equipment slot. One of `weapon`, `shield`, `armor`, `helmet`, `ring`, `necklace` | -
health | int | Health | -
damage | int | Damage | -

Item | Type | Description | Relations
-- | -- | -- | --
id | int | Item ID | PK
name | string | Item name | -
level | int | Item level | -
health | int | Health | -
damage | int | Damage | -
item_type_id | int | Item type | ItemType.id
inventory_id | int | FK of owning UserInventory | UserInventory.id
is_loot | boolean | Loot state | -

CharacterEquipment | Type | Description | Relations
-- | -- | -- | --
id | int | Equipment row ID | PK
character_id | int | Owning character | FK Character.id
item_id | int | Equipped item | FK Item.id, unique
slot | enum | Equipped slot | -

Encounter | Type | Description | Relations
-- | -- | -- | --
id | int | Encounter ID | PK
character_id | int | Player character | FK Character.id
enemy_type_id | int | Enemy type | FK EnemyType.id
enemy_level | int | Active dungeon enemy level | -
health | int | Current enemy health | -
damage | int | Current enemy damage | -

EnemyType | Type | Description | Relations
-- | -- | -- | --
id | int | Enemy type ID | PK
name | string | Name | -
description | string | Description | -
health | int | Health | -
damage | int | Damage | -
---

