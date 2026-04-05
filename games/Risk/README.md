# Risk

This project is deployed as a static web build served by `nginx`.

## Deployment behavior

The live site does not run the Python source code directly. It serves the generated files in `build/web`.

That means code changes will not appear in production until the web bundle is rebuilt.

## Updated Docker workflow

The Docker image now regenerates the web build during `docker build` by running:

```bash
python -m pygbag --build .
```

This keeps Render deployments in sync with the latest source code and avoids shipping a stale `build/web` folder from your local machine.

## Local build

If you want to generate the web version locally, install the build dependencies and run:

```bash
pip install -r requirements-web.txt
python -m pygbag --build .
```
