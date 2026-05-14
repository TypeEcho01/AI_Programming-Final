# Text Dungeon Crawler

A simple text-based dungeon crawler in Python with an extensible structure.

## Run

```bash
python3 dungeon_crawler.py
```

If a `dungeon_save.json` file exists, the game asks whether you want to continue that save or start a fresh run.

## Optional ChatGPT room generation

The `explore` command can call OpenAI's Responses API at runtime to create a new room. To enable live AI generation, set your API key before running the game:

```bash
export OPENAI_API_KEY="your-api-key"
python3 dungeon_crawler.py
```

You can optionally change the model with `OPENAI_MODEL`; otherwise the game uses `gpt-4o-mini`. If no API key is set, `explore` still creates a local fallback room so the game remains playable offline.

## Commands

- `help`
- `look`
- `go <direction>`
- `take <item>`
- `drop <item>`
- `shop`
- `buy <item>`
- `explore` / `generate`
- `attack`
- `use <item>`
- `unlock`
- `search`
- `map`
- `rest`
- `stats`
- `inventory`
- `save`
- `load` / `continue`
- `new`
- `quit`

## Current features

- Room graph with directional movement
- Runtime ChatGPT-powered room generation through the `explore` command
- Locked room flow (`unlock` + `lockpick`)
- Inventory and drop system
- Basic enemy combat with equipment effects and gold rewards
- Merchant shop for buying supplies with gold earned from defeated enemies
- Item usage (healing herb, potion, map, throwing dagger)
- Gold economy focused on combat rewards and shop spending
- Extra utility commands (`stats`, `map`, `rest`, `search`)
- Save/load support using a local `dungeon_save.json` file, including generated rooms
- Startup choice to continue saved progress or begin a new game

## Good base for expansion

The code is intentionally split into game state components (`Room`, `Player`, `DungeonGame`) so you can later add:

- More detailed AI prompts for procedural/dynamic room generation
- More enemy types and combat rules
- Quest systems
- Multiple save slots
- Event scripting
- More shops, item rarities, and NPC interactions
