# main.py — Phase 3 additions

1. Add imports at top of `apps/api/main.py`:

```python
from routers import dunning, analytics
import workers.scheduled  # registers Celery Beat schedule
```

2. Register routers (after existing includes):

```python
app.include_router(dunning.router,   prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
```

3. Start Celery Beat alongside your worker on Railway:

```bash
celery -A workers.celery_app beat --loglevel=info
```

(already configured in `railway.toml` as a separate service)
