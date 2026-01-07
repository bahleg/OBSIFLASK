OBSIFLASK supports multi-user mode, where each user has their own scope of available vaults.
Super-users (administrators) can adjust vault access and other rights for all users.
Each user can also change their visual theme and personalize settings related to the appearance of OBSIFLASK.

## 🚀 Multi-user regime demo
To start OBSIFLASK in multi-user mode, run `OBSIFLASK_AUTH_ENABLED="true" python3 -m obsiflask.main ./example/config.yml`.

If you use docker, you can run `docker run -e OBSIFLASK_AUTH="true"  -p 8000:8000 obsiflask:latest`.

See the [example config](https://github.com/bahleg/OBSIFLASK/blob/main/example/config.yml) for the details.

This will enable multi-user mode with a default super-user:

- **login**: root
- **password**: root

Other users can be created and managed via the Root panel.

## ⚠️ Attention
The work on the multi-user regime is still in progress, potentially the code can have some vulnerability.

**It's strongly recommend** to use some extra-layer of authorization, such as nginx if you plan to use this service in a public network.