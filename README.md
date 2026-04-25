# AI Interview App

## Run

From the project root:

```bash
uvicorn backend.main:app --reload
```

Then open:

```text
http://localhost:8000
```

## Structure

```text
backend/     FastAPI app and business logic
templates/   HTML pages
static/      CSS and JavaScript
temp/        Temporary uploaded audio files
```

## Notes

- `START.bat` starts the same app on Windows.
- The old React frontend has been removed from the runtime path.
