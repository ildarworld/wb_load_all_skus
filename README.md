# Wildberries SKU loader into CSV file

## How to install

1. Clone repo and:

```bash
python3 -m venv env
```

2. Activate virtual environment
   If you are using bash

```bash
source env/bin/activate
```

for fish shell:

```bash
source env/bin/activate.fish
```

3. Install dependecies

```bash
pip install -r requirements.txt
```

4. Rename .env file

```
mv .env.example .env
```

5. Properly fill token and supplier_id in the .env file
   If you need to load SKUs with errors, maintain appropriate environment variable in .env file

## Run

```bash
python loader.py
```
