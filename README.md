# Text Dungeon Crawler

A simple text-based dungeon crawler in Python with an extensible structure.

## Run

```bash
python3 dungeon_crawler.py
```

If a `dungeon_save.json` file exists, the game asks whether you want to continue that save or start a fresh run.

## Commands

- `help`
- `look`
- `go <direction>`
- `take <item>`
- `drop <item>`
- `shop`
- `buy <item>`
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
- Locked room flow (`unlock` + `lockpick`)
- Inventory and drop system
- Basic enemy combat with equipment effects and gold rewards
- Merchant shop for buying supplies with gold earned from defeated enemies
- Item usage (healing herb, potion, map, throwing dagger)
- Gold economy focused on combat rewards and shop spending
- Extra utility commands (`stats`, `map`, `rest`, `search`)
- Save/load support using a local `dungeon_save.json` file
- Startup choice to continue saved progress or begin a new game

## Good base for expansion

The code is intentionally split into game state components (`Room`, `Player`, `DungeonGame`) so you can later add:

- Procedural/dynamic room generation
- More enemy types and combat rules
- Quest systems
- Multiple save slots
- Event scripting
- More shops, item rarities, and NPC interactions
