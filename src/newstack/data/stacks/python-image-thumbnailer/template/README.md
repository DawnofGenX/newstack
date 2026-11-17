# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
.venv/bin/python -m {{ package_name }} thumbnail ./photo.jpg ./out.jpg --size 256x256
.venv/bin/python -m {{ package_name }} batch ./photos ./thumbs
```