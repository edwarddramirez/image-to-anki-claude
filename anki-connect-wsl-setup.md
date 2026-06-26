# AnkiConnect + WSL Setup

## 1. Install AnkiConnect in Anki (Windows)
- Tools → Add-ons → Get Add-ons
- Code: `2055492159`
- Restart Anki

## 2. Configure AnkiConnect to allow external connections
- Tools → Add-ons → AnkiConnect → Config
- Set `webBindAddress` to `"0.0.0.0"`
- Restart Anki

## 3. Enable mirrored networking in WSL
Create `C:\Users\<youruser>\.wslconfig` with:
```ini
[wsl2]
networkingMode=mirrored
```
Then restart WSL:
```powershell
wsl --shutdown
```

## 4. Verify
```bash
curl http://localhost:8765
# Expected: {"result": "AnkiConnect v.6", "error": null}
```

## 5. Use in Python
```python
import requests

ANKI_CONNECT = "http://localhost:8765"

def invoke(action, **params):
    return requests.post(ANKI_CONNECT,
        json={"action": action, "version": 6, "params": params}).json()
```
