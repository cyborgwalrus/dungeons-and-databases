# Backend API Documentation

## API Endpoints

| Resource name|Resource url|Resource description|Supported Methods| Implemented |
|:-----------: |:----------:|:------------------:|:---------------:|:-----------:|
|Login|`/login/signup`,<br>`/login/signin`|For creating user accounts and authenticating endpoints using the Flask-login library|`POST`| |
|User|`/users/`,<br>`/users/<int:user_id>`|For interacting with user accounts|`GET`,`PUT`,`DELETE`| |
|Character|`/characters/`,<br>`/characters/<int:character_id>`|For interacting player characters|`POST`,`GET`,`DELETE` | |
|Inventory|`/characters/<int:character_id>/inventory/`|For interacting with character inventory|`POST`,`GET`,`PUT`,`DELETE` | |
|Item|`/characters/<int:character_id/inventory/<int:item_id>`|For interacting with items in character inventory|`POST`,`GET`,`PUT`,`DELETE` | |
|Encounter|`/encounters/`,<br>`/encounters/<int:encounter_id>`|For interacting with dungeon encounters|`POST`,`GET`,`DELETE` | |