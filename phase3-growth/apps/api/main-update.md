# main.py Update — Phase 3

Add these lines to `apps/api/main.py`:

```python
from routers import dunning, analytics   # add to imports

app.include_router(dunning.router,    prefix=PREFIX)
app.include_router(analytics.router,  prefix=PREFIX)
```

Also import the scheduled tasks so Celery Beat picks them up:

```python
import workers.scheduled  # noqa — registers beat schedule
```
