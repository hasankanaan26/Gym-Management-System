# Alembic

Migrations for the gym app database.

```bash
# Generate a new migration after changing models:
alembic revision --autogenerate -m "describe change"

# Apply all migrations:
alembic upgrade head
```

For dev/demo we rely on `Base.metadata.create_all()` at app startup,
so no initial migration is included. Generate one the first time you
want to version the schema:

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
