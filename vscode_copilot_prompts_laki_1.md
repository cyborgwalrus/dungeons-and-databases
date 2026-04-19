# Copilot User Messages

1. i have modified backend structure and now the frontend is old. It is using old endpoints. I need to have login page, character select before the home page.

2. :8080/#/login:1 Access to fetch at 'http://localhost:5000/api/login/signup' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: Redirect is not allowed for a preflight request.

3. [Terminal 87d1882f-5798-4ea8-bd5d-d9db08242b01 notification: command completed with exit code 0. Use send_to_terminal to send another command or kill_terminal to stop it.]
   Terminal output:
   PS C:\Ohjelmointi\dungeons-and-databases> cd C:\Ohjelmointi\dungeons-and-databases\project ; docker compose down ; docker compose up -d --build
   [+] Running 3/3
    ✔ Container dnd_frontend       Removed                                    0.4s 
    ✔ Container dnd_backend        Removed                                   10.4s 
    ✔ Network project_dnd_network  Removed                                    0.4s 
   [+] Building 6.1s (22/22) FINISHED                                              
    => [internal] load local bake definitions                                 0.0s
    => => reading from stdin 1.06kB                                           0.0s
    => [frontend internal] load build definition from Dockerfile              0.0s
    => => transferring dockerfile: 234B                                       0.0s
    => [backend internal] load build definition from Dockerfile               0.0s
    => => transferring dockerfile: 406B                                       0.0s
    => [backend internal] load metadata for docker.io/library/python:3.11-sl  0.6s
    => [frontend internal] load metadata for docker.io/library/nginx:stable-  0.6s
    => [frontend internal] load .dockerignore                                 0.0s
    => => transferring context: 2B                                            0.0s
    => [backend internal] load .dockerignore                                  0.0s
    => => transferring context: 132B                                          0.0s
    => [frontend 1/3] FROM docker.io/library/nginx:stable-alpine@sha256:0272  0.1s
    => => resolve docker.io/library/nginx:stable-alpine@sha256:0272e4604ed93  0.1s
    => [frontend internal] load build context                                 0.3s
    => => transferring context: 326.10kB                                      0.2s
    => [backend 1/7] FROM docker.io/library/python:3.11-slim@sha256:233de067  0.1s
    => => resolve docker.io/library/python:3.11-slim@sha256:233de06753d30d12  0.1s
    => [backend internal] load build context                                  0.0s
    => => transferring context: 4.97kB                                        0.0s
    => CACHED [backend 2/7] COPY requirements.txt /app/requirements.txt       0.0s
    => CACHED [backend 3/7] RUN pip install --no-cache-dir -r /app/requireme  0.0s
    => [backend 4/7] COPY . /app/backend                                      0.1s
    => [backend 5/7] RUN chmod +x /app/backend/start-backend.sh               0.4s
    => CACHED [frontend 2/3] WORKDIR /usr/share/nginx/html                    0.0s
    => [frontend 3/3] COPY . /usr/share/nginx/html                            1.9s
    => [backend 6/7] WORKDIR /app                                             0.1s
    => [backend] exporting to image                                           0.6s
    => => exporting layers                                                    0.3s
    => => exporting manifest sha256:a88f1fad3e1e87152fbdd1085de9025be6416fc6  0.0s
    => => exporting config sha256:8b4bebf1729249b365f2a7c365e3a86d197fac0e42  0.0s
    => => exporting attestation manifest sha256:0b2cc45165be64a780fdbbf40d95  0.0s
    => => exporting manifest list sha256:b19db922e4357b84ed1ea487e2f2df74357  0.0s
    => => naming to docker.io/library/project-backend:latest                  0.0s
    => => unpacking to docker.io/library/project-backend:latest               0.1s
    => [backend] resolving provenance for metadata file                       0.0s
    => [frontend] exporting to image                                          2.7s
    => => exporting layers                                                    1.6s
    => => exporting manifest sha256:4db278675d6edfd5da8af973f2916e26857718dd  0.0s
    => => exporting config sha256:26fb3acd8748b59b07a2a65fc190796fa593ccb8af  0.0s
    => => exporting attestation manifest sha256:0747781270efc92201679aa96114  0.0s
    => => exporting manifest list sha256:bbb2363a2f3629d1ac00325a2c30417768b  0.0s
    => => naming to docker.io/library/project-frontend:latest                 0.0s
    => => unpacking to docker.io/library/project-frontend:latest              0.8s
    => [frontend] resolving provenance for metadata file                      0.0s
   [+] Running 5/5
    ✔ project-backend              Built                                      0.0s 
    ✔ project-frontend             Built                                      0.0s 
    ✔ Network project_dnd_network  Created                                    0.0s 
    ✔ Container dnd_backend        Started                                    0.5s 
    ✔ Container dnd_frontend       Started                                    0.5s

4. Access to fetch at 'http://localhost:5000/api/login/signup' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: Redirect is not allowed for a preflight request.Understand this error
   :5000/api/login/signup:1  Failed to load resource: net::ERR_FAILEDUnderstand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at HTMLButtonElement.<anonymous> (main.js:268:23)

5. api.js:5 
    GET http://localhost:5000/ net::ERR_TOO_MANY_REDIRECTS 302 (FOUND)
   fetchJson	@	api.js:5
   (anonymous)	@	main.js:268
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at HTMLButtonElement.<anonymous> (main.js:268:23)
   fetchJson	@	api.js:16
   await in fetchJson		
   (anonymous)	@	main.js:268

6. [Terminal ee687ed1-75ea-40a5-aebd-2f5767f4d1da notification: command completed with exit code 0. Use send_to_terminal to send another command or kill_terminal to stop it.]
   Terminal output:
   PS C:\Ohjelmointi\dungeons-and-databases> cd C:\Ohjelmointi\dungeons-and-databases\project ; docker compose down ; docker compose up -d --build
   [+] Running 3/3
    ✔ Container dnd_frontend       Removed                                    0.4s 
    ✔ Container dnd_backend        Removed                                   10.4s 
    ✔ Network project_dnd_network  Removed                                    0.4s 
   [+] Building 2.9s (22/22) FINISHED                                              
    => [internal] load local bake definitions                                 0.0s
    => => reading from stdin 1.06kB                                           0.0s
    => [frontend internal] load build definition from Dockerfile              0.0s
    => => transferring dockerfile: 234B                                       0.0s
    => [backend internal] load build definition from Dockerfile               0.0s
    => => transferring dockerfile: 406B                                       0.0s
    => [frontend internal] load metadata for docker.io/library/nginx:stable-  0.6s
    => [backend internal] load metadata for docker.io/library/python:3.11-sl  0.5s
    => [backend internal] load .dockerignore                                  0.0s
    => => transferring context: 132B                                          0.0s
    => [frontend internal] load .dockerignore                                 0.0s
    => => transferring context: 2B                                            0.0s
    => [backend 1/7] FROM docker.io/library/python:3.11-slim@sha256:233de067  0.1s
    => => resolve docker.io/library/python:3.11-slim@sha256:233de06753d30d12  0.1s
    => [backend internal] load build context                                  0.0s
    => => transferring context: 5.38kB                                        0.0s
    => [frontend 1/3] FROM docker.io/library/nginx:stable-alpine@sha256:0272  0.1s
    => => resolve docker.io/library/nginx:stable-alpine@sha256:0272e4604ed93  0.1s
    => [frontend internal] load build context                                 0.2s
    => => transferring context: 325.51kB                                      0.2s
    => CACHED [backend 2/7] COPY requirements.txt /app/requirements.txt       0.0s
    => CACHED [backend 3/7] RUN pip install --no-cache-dir -r /app/requireme  0.0s
    => [backend 4/7] COPY . /app/backend                                      0.1s
    => [backend 5/7] RUN chmod +x /app/backend/start-backend.sh               0.4s
    => CACHED [frontend 2/3] WORKDIR /usr/share/nginx/html                    0.0s
    => CACHED [frontend 3/3] COPY . /usr/share/nginx/html                     0.0s
    => [frontend] exporting to image                                          0.2s
    => => exporting layers                                                    0.0s
    => => exporting manifest sha256:19a7a2548bd30e8b7095530e2722717b6cbd75fc  0.0s
    => => exporting config sha256:c16c3f85c743e3d57c3890321e68dc296eeaec5bf9  0.0s
    => => exporting attestation manifest sha256:80aaf0860263412c1766cb0446c6  0.0s
    => => exporting manifest list sha256:cd45233e78d61f4b03749caa9dbf3801380  0.0s
    => => naming to docker.io/library/project-frontend:latest                 0.0s
    => => unpacking to docker.io/library/project-frontend:latest              0.0s
    => [backend 6/7] WORKDIR /app                                             0.1s
    => [backend] exporting to image                                           0.8s
    => => exporting layers                                                    0.4s
    => => exporting manifest sha256:1fe97c162231fcc49f54486effbf5610dc751f6a  0.0s
    => => exporting config sha256:5c3b79a10ceba3da34ec73d8ea3a95070fbd6de3a1  0.0s
    => => exporting attestation manifest sha256:baf89875042322b93f9d621322ff  0.1s
    => => exporting manifest list sha256:9b0087da372cf5ba3380f2a62462860c09b  0.0s
    => => naming to docker.io/library/project-backend:latest                  0.0s
    => => unpacking to docker.io/library/project-backend:latest               0.1s
    => [frontend] resolving provenance for metadata file                      0.0s
    => [backend] resolving provenance for metadata file                       0.0s
   [+] Running 5/5
    ✔ project-backend              Built                                      0.0s 
    ✔ project-frontend             Built                                      0.0s 
    ✔ Network project_dnd_network  Created                                    0.1s 
    ✔ Container dnd_backend        Started                                    0.5s 
    ✔ Container dnd_frontend       Started                                    0.6s

7. :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:27)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory/equipped' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/equipped net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:52)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory/items' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/items net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:86)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/player 400 (BAD REQUEST)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  PUT http://localhost:5000/api/player 400 (BAD REQUEST)
   fetchJson @ api.js:5
   renderHome @ main.js:394
   await in renderHome
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/player 400 (BAD REQUEST)

8. do not disable character endpoint login requirements

9. [Terminal 814c7928-720b-41f4-ac8c-9c800b923fad notification: command completed with exit code 0. Use send_to_terminal to send another command or kill_terminal to stop it.]
   Terminal output:
   PS C:\Ohjelmointi\dungeons-and-databases> cd C:\Ohjelmointi\dungeons-and-databases\project ; docker compose up -d --build
   [+] Building 2.9s (22/22) FINISHED                                              
    => [internal] load local bake definitions                                 0.0s
    => => reading from stdin 1.06kB                                           0.0s
    => [backend internal] load build definition from Dockerfile               0.0s
    => => transferring dockerfile: 406B                                       0.0s
    => [frontend internal] load build definition from Dockerfile              0.0s
    => => transferring dockerfile: 234B                                       0.0s
    => [frontend internal] load metadata for docker.io/library/nginx:stable-  0.8s
    => [backend internal] load metadata for docker.io/library/python:3.11-sl  0.8s
    => [backend internal] load .dockerignore                                  0.0s
    => => transferring context: 132B                                          0.0s
    => [frontend internal] load .dockerignore                                 0.0s
    => => transferring context: 2B                                            0.0s
    => [backend 1/7] FROM docker.io/library/python:3.11-slim@sha256:233de067  0.1s
    => => resolve docker.io/library/python:3.11-slim@sha256:233de06753d30d12  0.1s
    => [backend internal] load build context                                  0.0s
    => => transferring context: 5.84kB                                        0.0s
    => [frontend 1/3] FROM docker.io/library/nginx:stable-alpine@sha256:0272  0.1s
    => => resolve docker.io/library/nginx:stable-alpine@sha256:0272e4604ed93  0.1s
    => [frontend internal] load build context                                 0.3s
    => => transferring context: 325.51kB                                      0.2s
    => CACHED [backend 2/7] COPY requirements.txt /app/requirements.txt       0.0s
    => CACHED [backend 3/7] RUN pip install --no-cache-dir -r /app/requireme  0.0s
    => [backend 4/7] COPY . /app/backend                                      0.1s
    => [backend 5/7] RUN chmod +x /app/backend/start-backend.sh               0.4s
    => CACHED [frontend 2/3] WORKDIR /usr/share/nginx/html                    0.0s
    => CACHED [frontend 3/3] COPY . /usr/share/nginx/html                     0.0s
    => [frontend] exporting to image                                          0.2s
    => => exporting layers                                                    0.0s
    => => exporting manifest sha256:a4883364ed51d8c735558fd6c50ccafc799de1e3  0.0s
    => => exporting config sha256:740c9d1d6535c9c15ca1bba7e2765dee5588899384  0.0s
    => => exporting attestation manifest sha256:aae2f7efdc13c45db35498054350  0.1s
    => => exporting manifest list sha256:ef1ef663ddeb4bc4d959d6f014a2e314b66  0.0s
    => => naming to docker.io/library/project-frontend:latest                 0.0s
    => => unpacking to docker.io/library/project-frontend:latest              0.0s
    => [backend 6/7] WORKDIR /app                                             0.1s
    => [backend] exporting to image                                           0.6s
    => => exporting layers                                                    0.4s
    => => exporting manifest sha256:dff411bab2f5e44ec964b4a672bdf2c0daf17277  0.0s
    => => exporting config sha256:b187dd380ff0628039007f619f61e5eac1f638dbf3  0.0s
    => => exporting attestation manifest sha256:ba8dd336d9218a6501fef96b21b4  0.1s
    => => exporting manifest list sha256:ffaaa43e6e99f1abe4458d85cbeccb1f667  0.0s
    => => naming to docker.io/library/project-backend:latest                  0.0s
    => => unpacking to docker.io/library/project-backend:latest               0.1s
    => [frontend] resolving provenance for metadata file                      0.0s
    => [backend] resolving provenance for metadata file                       0.0s
   [+] Running 4/4
    ✔ project-backend         Built                                           0.0s 
    ✔ project-frontend        Built                                           0.0s 
    ✔ Container dnd_backend   Started                                        11.3s 
    ✔ Container dnd_frontend  Started                                         1.0s

10. GET http://localhost:8080/favicon.ico 404 (Not Found)Understand this error
   api.js:5  POST http://localhost:5000/api/login/signin 401 (UNAUTHORIZED)
   fetchJson @ api.js:5
   (anonymous) @ main.js:246Understand this error
   :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:27)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory/equipped' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/equipped net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:52)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   :8080/#/:1 Access to fetch at 'http://localhost:5000/api/inventory/items' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/items net::ERR_FAILED
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error TypeError: Failed to fetch
       at fetchJson (api.js:5:23)
       at loadStateAndRenderPartial (main.js:194:86)
       at Object.renderHome (main.js:387:9)
       at showHome (home.js:3:23)
       at route (main.js:480:58)
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/player 400 (BAD REQUEST)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  PUT http://localhost:5000/api/player 400 (BAD REQUEST)
   fetchJson @ api.js:5
   renderHome @ main.js:394
   await in renderHome
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/player 400 (BAD REQUEST)

11. check ensure player again

12. Access to fetch at 'http://localhost:5000/api/inventory' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.

13. api.js:5  GET http://localhost:5000/api/inventory/equipped 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/inventory 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/items 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON

14. api.js:5  GET http://localhost:5000/api/inventory/equipped 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/inventory 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson @ api.js:16
   await in fetchJson
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:5  GET http://localhost:5000/api/inventory/items 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   loadStateAndRenderPartial @ main.js:194
   renderHome @ main.js:387
   showHome @ home.js:3
   route @ main.js:480
   hashchange
   navigateTo @ main.js:460
   (anonymous) @ main.js:334Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON

15. inventory.js:21 Uncaught (in promise) TypeError: Cannot read properties of undefined (reading 'name')
       at inventory.js:21:20
       at Array.sort (<anonymous>)
       at renderInventoryGrid (inventory.js:13:42)
       at renderInventoryGrid (main.js:128:10)
       at loadStateAndRenderPartial (main.js:226:3)
       at async Object.renderHome (main.js:413:3)

16. Access to fetch at 'http://localhost:5000/api/characters/1/inventory' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: Redirect is not allowed for a preflight request.
   
   i tried to equip an item

17. -preseeded items dont have every item for each slot
   - unequipp all items isnt working 
   - equip best items isnt working
   - item stats are shown as zero

18. change item icons to use item slots not stats

19. - preseeded items are not working correctly: i need each item for each slot. I got 5 swords and 2 shields
   
   - bonus health and bonus attack isnt updating to overall health and damage
   
   - dropping items back to inventory is makes them disappear
   - dropping items to destroy doesnt work

20. - drop items to destroy isnt destroying any items.
   - update also current health with bonus health

21. max health is updating correctly but current health isnt. When i unequip all items the current health is updating. It should be updated with max health

22. before equipping -> 100 / 100
   after equipping -> 100 / 168
   after unequipping -> 168 / 100

23. GET http://localhost:5000/api/dungeon/encounter 405 (METHOD NOT ALLOWED)
   fetchJson @ api.js:5
   renderDungeon @ main.js:488
   showDungeon @ dungeon.js:3
   route @ main.js:539
   hashchange
   navigateTo @ main.js:518
   (anonymous) @ main.js:433Understand this error
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON

24. GET http://localhost:8080/favicon.ico 404 (Not Found)
   api.js:5 
    GET http://localhost:5000/api/dungeon/encounters/ 500 (INTERNAL SERVER ERROR)
   fetchJson	@	api.js:5
   renderDungeon	@	main.js:488
   showDungeon	@	dungeon.js:3
   route	@	main.js:539
   hashchange		
   navigateTo	@	main.js:518
   (anonymous)	@	main.js:433
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson	@	api.js:16
   await in fetchJson		
   renderDungeon	@	main.js:488
   showDungeon	@	dungeon.js:3
   route	@	main.js:539
   hashchange		
   navigateTo	@	main.js:518
   (anonymous)	@	main.js:433

25. GET http://localhost:5000/api/dungeon/encounters/1/current 500 (INTERNAL SERVER ERROR)
   fetchJson	@	api.js:5
   renderDungeon	@	main.js:498
   await in renderDungeon		
   showDungeon	@	dungeon.js:3
   route	@	main.js:548
   hashchange		
   navigateTo	@	main.js:527
   (anonymous)	@	main.js:433
   api.js:16 Fetch error SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
   fetchJson	@	api.js:16
   await in fetchJson		
   renderDungeon	@	main.js:498
   await in renderDungeon		
   showDungeon	@	dungeon.js:3
   route	@	main.js:548
   hashchange		
   navigateTo	@	main.js:527
   (anonymous)	@	main.js:433

26. i am in old character. after creating new character, it will not update the session and hold the old characters homescreen.

27. creating new character, the preseeded items are bit wrong: silver necklace is already updated to +2. I have 2 iron shiels and no armor

28. update the player stats header to player name

