# Text Dungeon Crawler

A simple text-based dungeon crawler in Python with an extensible structure.

## Run

```bash
python3 dungeon_crawler.py
```

## Commands

- `help`
- `look`
- `go <direction>`
- `take <item>`
- `drop <item>`
- `attack`
- `use <item>`
- `unlock`
- `search`
- `map`
- `rest`
- `stats`
- `inventory`
- `quit`

## Current features

- Room graph with directional movement
- Locked room flow (`unlock` + `lockpick`)
- Inventory and drop system
- Basic enemy combat with equipment effects
- Item usage (healing herb, potion, map)
- Gold economy through loot, combat, and searching
- Extra utility commands (`stats`, `map`, `rest`, `search`)

## Good base for expansion

The code is intentionally split into game state components (`Room`, `Player`, `DungeonGame`) so you can later add:

- Procedural/dynamic room generation
- More enemy types and combat rules
- Quest systems
- Save/load support
- Event scripting
- Shops and NPC interactions
