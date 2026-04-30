# Text Dungeon Crawler

A simple text-based dungeon crawler in Python with an extensible structure.

## Run

```bash
python3 dungeon_crawler.py
```

## Current features

- Room graph with directional movement
- Inventory system
- Basic enemy combat
- Item usage (healing item)
- Command parser

## Good base for expansion

The code is intentionally split into game state components (`Room`, `Player`, `DungeonGame`) so you can later add:

- Procedural/dynamic room generation
- More enemy types and combat rules
- Quest systems
- Save/load support
- Event scripting
