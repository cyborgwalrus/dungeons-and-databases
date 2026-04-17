# Database

## Overview

The game backend's database consists of following entities: User, Character, Item, ItemType, EnemyType and Encounter.

The relationships between tables were defined using foreign keys in the database schema, and are extended with SQLAlchemy relationships to populate related objects in JSON responses.

# Database design and implementation

![alt text](docs/database-schema.png)

## Database design

### User

The User table represents a player account. Each user has a unique username, a password and can own multiple characters. Username and password will be used to login and obtain an API token for authenticating with the APIs endpoints.

### Character

The Character table represents a playable character. Each character belongs to a user and contains basic attributes such as level, health, and damage. Each character has an inventory, a list of Items the character has looted from the dungeon. One item of each type can be equipped to increase the character's stats.

### ItemType

The ItemType table defines item templates that store static item attributes.
When the player receives loot in a dungeon, an ItemType template is instantiated into an Item object with additional dynamic fields.

### Item

A table of items that players have looted from the dungeon. Each Item is connected to one ItemType template and one Character that owns the item. The player can combine multiple items together to create a new item with a high level attribute that will be used in damage calculations. When a character equips and item, its is_equipped flag is set to true, applying its bonus stats to the character. When an item is dropped in the dungeon, it starts with its is_loot flag set to true. If the player is defeated during a dungeon run, all items marked with is_loot are deleted from their inventory.

### Encounter

When the player enters a dungeon, an Encounter entry is created and connected to the player character using a foreign key. An EnemyType is chosen at random to face the player character, and the EnemyType entry's base_health and base_damage values are scaled to player level and stored in the Encounter's enemy_health and enemy_damage fields.

### EnemyType

A table holding monster templates. Each EnemyType entry has an id, name, description, base_health and base_damage.

---

User | Type | Description | Relations
-- | -- | -- | --
id | int | User ID | PK
username | string | Username | unique
password | string | Password |  


Character | Type | Description | Relations
-- | -- | -- | --
id | int | Character ID | PK
user_id | int | Owning User's id | FK User.id
name | string | Name |  
level | int | Level |  
health | int | Health |  
damage | int | Damage |  

ItemType | Type | Description | Relations
-- | -- | -- | --
id | int | Item type ID | PK
name | string | Item name |  
slot | enum | Equipment slot. One of `weapon`, `shield`, `armor`, `helmet`, `ring`, `necklace` | 
base_health_bonus | int | Base health bonus |  
base_damage_bonus | int | Base damage bonus |  

Item | Type | Description | Relations
-- | -- | -- | --
id | int | Item ID | PK
name | string | Item name |  
level | int | Item level |  
health_bonus | int | Health bonus |  
damage_bonus | int | Damage bonus |  
item_type_id | int | Item type |  ItemType.id
owner_id | int | FK of owning Character| Character.id
is_equipped | boolean | Equipped state |  
is_loot | boolean | Loot state |  

Encounter | Type | Description | Relations
-- | -- | -- | --
id | int | Encounter ID | PK
character_id | int | Player character | FK Character.id
enemy_type_id | int | Enemy type | FK EnemyType.id
enemy_health | int | Current enemy health |  
enemy_damage | int | Current enemy damage |  

EnemyType | Type | Description | Relations
-- | -- | -- | --
id | int | Enemy type ID | PK
name | string | Name |  
description | string | Description |  
base_health | int | Base health |  
base_damage | int | Base damage |  

---

