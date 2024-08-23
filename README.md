# stopdb

Stop Hate In Schools -- backend database + administrative UI.

To run locally, first install [Astral's `uv`](https://github.com/astral-sh/uv). Then:

```
> cp .env.sample .env
> uv run manage.py migrate
> uv run manage.py createsuperuser
> uv run manage.py runserver
```

And visit http://localhost:8000/admin/
