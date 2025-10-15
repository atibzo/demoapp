# Instructions to Debug the Issue

## Step 1: Restart the Web Container
In your terminal (where you ran docker compose), run:

```bash
docker compose restart web
```

Wait for it to say "Ready" (should take ~10-20 seconds).

## Step 2: Hard Refresh Your Browser
- **Mac**: Press `Cmd + Shift + R`
- **Windows/Linux**: Press `Ctrl + Shift + R`

## Step 3: Open Browser Console
1. Press `F12` (or `Cmd + Option + I` on Mac)
2. Go to the "Console" tab
3. Clear any old messages (click the 🚫 icon or type `clear()`)

## Step 4: Test Historical Data
1. Switch to "Historical Data" radio button
2. Select a date (e.g., 2025-10-10)
3. Click "Run Scan"

## Step 5: Check Console Output
You should see logs like:
```
Run Scan clicked - dataMode: HISTORICAL date: 2025-10-10
TopAlgos refresh - dataMode: HISTORICAL historicalDate: 2025-10-10
Historical fetch response: 200 true
Historical data received: 5 rows
Setting rows: [...]
Rendering table - rows.length: 5
```

## If Still Nothing Happens

Try a full restart:
```bash
docker compose down
docker compose up -d
docker compose logs -f web
```

Then repeat steps 2-4.
