# Copilot User Messages

1. Rewrite the current prototype backend to match the new database models and API endpoint documentation

2. Continue, but ignore the frontend. It will be rewritten seperately

3. Do not modify models.py any further

4. - I have updated the endpoint documentation and added database.md for more context
   - Concider that ItemType is a static template that will be used instantiated into an Item with additional dynamic fields. When an item is created, it inherits its health and damage bonus

5. seperate player_routes into character_routes and user_routes

6. Move these to their own .csv files

7. try again. move these to their own .csv files

8. - move the api routes into routes folder
   - rename "enemy_seeds.csv" to "enemy_types.csv" and "item_type_seeds.csv" to "item_types.csv"

9. - for views with two api endpoints defined, remove the one that doesnt match the API endpoint documentation. Each view should have only one endpoint, with the /api/ prefix injected for all routes in app.py

10. update api to match documentation

11. Do a refactoring pass on the backend.
   - remove code duplication
   - remove dead code
   - use helper functions to shorten long routes
   - tell me about other ways to make the code cleaner

12. continue cleanup, but dont add tests yet

13. continue cleanup

14. continue cleaning up reforge loop, combat math and request parsing/error responses

15. continue cleanup

16. continue cleanup

17. Simplify bonus health and damage logic
   - Character bonus_health and bonus_damage are calculated from health_bonus and damage_bonus of equipped items
   - When an Item is created, it inherits its bonus_damage and bonus_health from it's linked ItemType template
   - When items are reforged, 3 items of the same type and level are destroyed and replaced with an item of the same type, but +1 level and twice the bonus_health and bonus_damage

18. add type hints to helper functions

19. Use the models from models.py in type hints where appropriate

20. remove the need for _models_module(). It is preventing some type hints from working

21. remove Item descriptions

22. remove description from ItemType model as well, and any related code in helper functions

23. move files related to the database into folder

24. rename the folder to db

25. move the models.py as well

26. you didnt actually create the init.py

27. change auth and login to use Flask-Login package

28. add login requirement for all endpoints

29. move csv loading and database seeding logic from app.py to db/init-db.py

30. remove the need for importlib. The seed data will not change during runtime

31. Update the tables in readmes to match current code

32. - remove /api/demo/inventory endpoint, the items are seeded in character creation
   - add /api/player to readme table

33. add missing endpoints and methods to table

34. Keep the old layout, one top level resource per row

35. Seperate resource urls with <br>

36. Update endpoints table:
   - remove supported methods column and move the supported methods to
    the resource url. Use format `/example` - `POST` `GET`

