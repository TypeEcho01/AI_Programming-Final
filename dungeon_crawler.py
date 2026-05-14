from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


SAVE_FILE = Path("dungeon_save.json")
SAVE_VERSION = 1
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
MAX_AI_ROOMS = 5


ENEMY_GOLD_REWARDS = {
    "cult acolyte": 8,
    "skeletal guardian": 18,
    "wandering rat": 3,
}


DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


@dataclass
class Room:
    """A location in the dungeon graph."""

    name: str
    description: str
    exits: Dict[str, "Room"] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)
    enemy: Optional[str] = None
    locked: bool = False
    lock_reason: str = ""
    shop_items: Dict[str, int] = field(default_factory=dict)
    ai_generated: bool = False

    def connect(self, direction: str, other: "Room") -> None:
        """Create a bidirectional connection between rooms."""
        if direction not in DIRECTIONS:
            raise ValueError(f"Unsupported direction: {direction}")

        opposite = DIRECTIONS[direction]
        self.exits[direction] = other
        other.exits[opposite] = self


@dataclass
class Player:
    current_room: Room
    hp: int = 20
    max_hp: int = 20
    inventory: List[str] = field(default_factory=list)
    gold: int = 0


class DungeonGame:
    """Simple, extensible text dungeon crawler."""

    def __init__(self) -> None:
        self.rooms = self._build_world()
        self.player = Player(current_room=self.rooms["Entrance"])
        self.running = True

    def _build_world(self) -> Dict[str, Room]:
        """Create a tiny handcrafted dungeon.

        This is intentionally separated so future versions can swap in
        procedural generation.
        """
        entrance = Room(
            "Entrance",
            "A cold stone archway. A faded rune glows above you.",
            items=["torch", "small potion"],
        )
        hall = Room(
            "Hall",
            "An echoing hall lined with cracked statues.",
            items=["lockpick"],
        )
        merchant = Room(
            "Merchant Nook",
            "A nervous goblin merchant has set up a blanket of useful supplies.",
            shop_items={
                "healing herb": 5,
                "small potion": 9,
                "lockpick": 7,
                "throwing dagger": 10,
            },
        )
        armory = Room(
            "Armory",
            "Rusty blades hang on hooks. One still looks usable.",
            items=["iron sword", "wooden shield"],
        )
        shrine = Room(
            "Shrine",
            "A forgotten shrine hums with strange energy.",
            items=["healing herb"],
            enemy="cult acolyte",
        )
        vault = Room(
            "Vault",
            "An iron vault door stands open. Treasure glitters inside.",
            items=["ancient coin", "ruby idol", "old map"],
            enemy="skeletal guardian",
            locked=True,
            lock_reason="A heavy gate blocks the way. Maybe a lockpick could open it.",
        )

        entrance.connect("north", hall)
        hall.connect("west", merchant)
        hall.connect("east", armory)
        hall.connect("north", shrine)
        shrine.connect("east", vault)

        return {
            room.name: room
            for room in [entrance, hall, merchant, armory, shrine, vault]
        }

    def start(self) -> None:
        print("Welcome to the Dungeon Crawler!")
        print("Type 'help' for commands. Type 'quit' to leave.\n")
        self.look()

        while self.running:
            command = input("\n> ").strip().lower()
            self._handle_command(command)

            if self.player.hp <= 0:
                print("\nYou collapse. Game over.")
                self.running = False

    def _handle_command(self, command: str) -> None:
        if not command:
            return

        parts = command.split()
        verb = parts[0]
        args = parts[1:]

        match verb:
            case "help":
                self.help()
            case "look":
                self.look()
            case "go":
                if not args:
                    print("Go where? (north/south/east/west)")
                else:
                    self.move(args[0])
            case "take":
                if not args:
                    print("Take what?")
                else:
                    self.take(" ".join(args))
            case "shop":
                self.show_shop()
            case "buy":
                if not args:
                    print("Buy what?")
                else:
                    self.buy(" ".join(args))
            case "explore" | "generate":
                self.generate_ai_room()
            case "drop":
                if not args:
                    print("Drop what?")
                else:
                    self.drop(" ".join(args))
            case "attack":
                self.attack()
            case "inventory":
                self.show_inventory()
            case "use":
                if not args:
                    print("Use what?")
                else:
                    self.use_item(" ".join(args))
            case "stats":
                self.stats()
            case "save":
                self.save_game()
            case "load" | "continue":
                if self.load_game():
                    self.look()
            case "new":
                self.new_game()
            case "search":
                self.search()
            case "rest":
                self.rest()
            case "unlock":
                self.unlock()
            case "map":
                self.show_map()
            case "quit" | "exit":
                print("You leave the dungeon. Use 'save' first if you want to keep progress.")
                self.running = False
            case _:
                print("Unknown command. Type 'help' for options.")

    def help(self) -> None:
        print(
            "Commands: help, look, go <direction>, take <item>, drop <item>, "
            "shop, buy <item>, explore, attack, use <item>, unlock, search, map, "
            "rest, stats, inventory, save, load, new, quit"
        )

    def look(self) -> None:
        room = self.player.current_room
        print(f"\n== {room.name} ==")
        print(room.description)

        if room.enemy:
            print(f"Enemy present: {room.enemy}")

        if room.items:
            print("You see:", ", ".join(room.items))

        if room.shop_items:
            print("A shop is here. Type 'shop' to see what is for sale.")

        if self._available_ai_directions(room):
            print("Unmapped passages nearby. Type 'explore' to generate a new room.")

        if room.exits:
            print("Exits:", ", ".join(room.exits.keys()))

    def move(self, direction: str) -> None:
        room = self.player.current_room
        target = room.exits.get(direction)

        if not target:
            print("You can't go that way.")
            return

        if target.locked:
            print(target.lock_reason)
            return

        self.player.current_room = target
        self.look()

    def take(self, item_name: str) -> None:
        room = self.player.current_room
        lowered = {item.lower(): item for item in room.items}

        if item_name not in lowered:
            print("That item isn't here.")
            return

        real_name = lowered[item_name]
        room.items.remove(real_name)

        self.player.inventory.append(real_name)
        print(f"You took {real_name}.")

    def drop(self, item_name: str) -> None:
        lowered = {item.lower(): item for item in self.player.inventory}
        if item_name not in lowered:
            print("You don't have that item.")
            return

        real_name = lowered[item_name]
        self.player.inventory.remove(real_name)
        self.player.current_room.items.append(real_name)
        print(f"You dropped {real_name}.")

    def _available_ai_directions(self, room: Room) -> List[str]:
        return [direction for direction in DIRECTIONS if direction not in room.exits]

    def _ai_room_count(self) -> int:
        return sum(room.ai_generated for room in self.rooms.values())

    def generate_ai_room(self) -> None:
        room = self.player.current_room
        directions = self._available_ai_directions(room)
        if not directions:
            print("There are no unmapped passages from here.")
            return

        if self._ai_room_count() >= MAX_AI_ROOMS:
            print("The dungeon resists further expansion for now.")
            return

        direction = random.choice(directions)
        room_data = self._request_ai_room_data(room, direction)
        if room_data is None:
            room_data = self._fallback_ai_room_data(room, direction)
            print("AI room generation is unavailable, so the dungeon shifts on its own.")
        else:
            print("ChatGPT dreams a new chamber into the dungeon...")

        name = self._unique_room_name(room_data["name"])
        new_room = Room(
            name,
            room_data["description"],
            items=room_data["items"],
            enemy=room_data["enemy"],
            ai_generated=True,
        )
        room.connect(direction, new_room)
        self.rooms[new_room.name] = new_room
        print(f"A new passage opens {direction} to {new_room.name}.")
        self.player.current_room = new_room
        self.look()

    def _request_ai_room_data(self, room: Room, direction: str) -> Optional[Dict[str, object]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        prompt = (
            "Create one compact text dungeon room as JSON only. "
            "Schema: name string, description string, items array of strings, "
            "enemy string or null. Keep names under 5 words. Use 0-2 items from "
            "this list only: healing herb, small potion, lockpick, throwing dagger, "
            "ancient coin, torch. Use enemies only from: wandering rat, cult acolyte, "
            "skeletal guardian, or null. "
            f"The player is exploring {direction} from {room.name}: {room.description}"
        )
        payload = {
            "model": model,
            "input": prompt,
            "max_output_tokens": 250,
        }
        request = urllib.request.Request(
            OPENAI_RESPONSES_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            print(f"AI generation failed: {error}")
            return None

        output_text = self._strip_json_fence(self._extract_response_text(response_data))
        if not output_text:
            return None

        try:
            raw_room = json.loads(output_text)
        except json.JSONDecodeError:
            print("AI generation returned text that was not valid JSON.")
            return None

        return self._coerce_ai_room_data(raw_room)

    def _extract_response_text(self, response_data: Dict[str, object]) -> str:
        direct_text = response_data.get("output_text")
        if isinstance(direct_text, str):
            return direct_text.strip()

        output_items = response_data.get("output", [])
        if not isinstance(output_items, list):
            return ""

        text_parts = []
        for item in output_items:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    text_parts.append(content["text"])
        return "".join(text_parts).strip()

    def _strip_json_fence(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped

        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _coerce_ai_room_data(self, raw_room: object) -> Dict[str, object]:
        allowed_items = {
            "healing herb",
            "small potion",
            "lockpick",
            "throwing dagger",
            "ancient coin",
            "torch",
        }
        allowed_enemies = set(ENEMY_GOLD_REWARDS) | {None}

        if not isinstance(raw_room, dict):
            raw_room = {}

        name = str(raw_room.get("name") or "Shifting Chamber")[:40]
        description = str(
            raw_room.get("description")
            or "A half-formed chamber settles into place around you."
        )[:240]
        raw_items = raw_room.get("items", [])
        if not isinstance(raw_items, list):
            raw_items = []
        items = [str(item) for item in raw_items if str(item) in allowed_items][:2]
        enemy = raw_room.get("enemy")
        if enemy not in allowed_enemies:
            enemy = None

        return {
            "name": name,
            "description": description,
            "items": items,
            "enemy": enemy,
        }

    def _fallback_ai_room_data(self, room: Room, direction: str) -> Dict[str, object]:
        themes = [
            ("Mosslit Grotto", "Soft green moss lights a damp cavern beyond the old stonework."),
            ("Clockwork Cell", "Broken brass gears tick inside the walls like a dying heart."),
            ("Ash Library", "Shelves of burned books crumble whenever you breathe too loudly."),
            ("Mirror Crypt", "Clouded mirrors reflect figures that are not standing behind you."),
        ]
        name, description = random.choice(themes)
        possible_items = [[], ["healing herb"], ["small potion"], ["torch"], ["ancient coin"]]
        possible_enemies = [None, "wandering rat", None, "cult acolyte"]
        return {
            "name": name,
            "description": f"{description} It appeared while exploring {direction} from {room.name}.",
            "items": random.choice(possible_items),
            "enemy": random.choice(possible_enemies),
        }

    def _unique_room_name(self, base_name: str) -> str:
        if base_name not in self.rooms:
            return base_name

        suffix = 2
        while f"{base_name} {suffix}" in self.rooms:
            suffix += 1
        return f"{base_name} {suffix}"

    def show_shop(self) -> None:
        room = self.player.current_room
        if not room.shop_items:
            print("There is no shop here.")
            return

        print("For sale:")
        for item, price in room.shop_items.items():
            print(f"- {item}: {price} gold")
        print(f"Your gold: {self.player.gold}")
        print("Use 'buy <item>' to purchase supplies.")

    def buy(self, item_name: str) -> None:
        room = self.player.current_room
        lowered = {item.lower(): item for item in room.shop_items}

        if not lowered:
            print("There is no shop here.")
            return

        if item_name not in lowered:
            print("That item is not for sale here.")
            return

        real_name = lowered[item_name]
        price = room.shop_items[real_name]
        if self.player.gold < price:
            print(
                f"You need {price} gold to buy {real_name}. "
                f"You only have {self.player.gold}."
            )
            return

        self.player.gold -= price
        self.player.inventory.append(real_name)
        print(f"You bought {real_name} for {price} gold. Gold left: {self.player.gold}")

    def attack(self) -> None:
        room = self.player.current_room
        if not room.enemy:
            print("Nothing to attack here.")
            return

        player_roll = random.randint(2, 8)
        enemy_roll = random.randint(1, 6)

        if "iron sword" in self.player.inventory:
            player_roll += 2

        if player_roll >= enemy_roll:
            reward = ENEMY_GOLD_REWARDS.get(room.enemy, 4)
            print(f"You defeated the {room.enemy}!")
            room.enemy = None
            self.player.gold += reward
            print(f"You collect {reward} gold from the remains.")
        else:
            damage = random.randint(2, 5)
            if "wooden shield" in self.player.inventory:
                damage = max(1, damage - 1)
            self.player.hp -= damage
            print(f"The {room.enemy} hits you for {damage} damage. HP: {self.player.hp}")

    def use_item(self, item_name: str) -> None:
        lowered = {item.lower(): item for item in self.player.inventory}
        if item_name not in lowered:
            print("You don't have that item.")
            return

        real_name = lowered[item_name]

        if real_name == "healing herb":
            heal = 6
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.player.inventory.remove(real_name)
            print(f"You use the healing herb and recover HP. HP: {self.player.hp}")
        elif real_name == "small potion":
            heal = 10
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.player.inventory.remove(real_name)
            print(f"You drink the small potion and recover HP. HP: {self.player.hp}")
        elif real_name == "old map":
            self.show_map()
        elif real_name == "throwing dagger":
            self.player.inventory.remove(real_name)
            if self.player.current_room.enemy:
                reward = ENEMY_GOLD_REWARDS.get(self.player.current_room.enemy, 4)
                print(f"You throw the dagger and defeat the {self.player.current_room.enemy}!")
                self.player.current_room.enemy = None
                self.player.gold += reward
                print(f"You collect {reward} gold from the remains.")
            else:
                print("You toss the dagger into the shadows, but there is no enemy here.")
        else:
            print(f"You can't use {real_name} right now.")

    def unlock(self) -> None:
        room = self.player.current_room
        locked_neighbors = [r for r in room.exits.values() if r.locked]
        if not locked_neighbors:
            print("There is nothing nearby to unlock.")
            return

        if "lockpick" not in self.player.inventory:
            print("You need a lockpick to unlock this path.")
            return

        target = locked_neighbors[0]
        target.locked = False
        print(f"You unlock access to {target.name}.")

    def save_game(self) -> None:
        """Write the current player and room state to disk."""
        save_data = {
            "version": SAVE_VERSION,
            "player": {
                "current_room": self.player.current_room.name,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "inventory": self.player.inventory,
                "gold": self.player.gold,
            },
            "rooms": {
                name: {
                    "name": room.name,
                    "description": room.description,
                    "items": room.items,
                    "enemy": room.enemy,
                    "locked": room.locked,
                    "lock_reason": room.lock_reason,
                    "shop_items": room.shop_items,
                    "ai_generated": room.ai_generated,
                    "exits": {
                        direction: target.name
                        for direction, target in room.exits.items()
                    },
                }
                for name, room in self.rooms.items()
            },
        }

        SAVE_FILE.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
        print(f"Game saved to {SAVE_FILE}.")

    def load_game(self) -> bool:
        """Load player and mutable room state from disk."""
        if not SAVE_FILE.exists():
            print("No saved game found. Start exploring, then use 'save'.")
            return False

        try:
            save_data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("Save file is damaged and could not be loaded.")
            return False

        if save_data.get("version") != SAVE_VERSION:
            print("Save file version is not compatible with this game build.")
            return False

        player_data = save_data.get("player", {})
        room_data = save_data.get("rooms", {})
        current_room_name = player_data.get("current_room", "Entrance")

        self.rooms = self._build_world()
        for name, saved_room in room_data.items():
            if not isinstance(saved_room, dict):
                continue
            if name not in self.rooms:
                self.rooms[name] = Room(
                    saved_room.get("name", name),
                    saved_room.get("description", "A restored chamber from your save."),
                )

        for name, saved_room in room_data.items():
            room = self.rooms.get(name)
            if not room or not isinstance(saved_room, dict):
                continue
            room.description = str(saved_room.get("description", room.description))
            room.items = list(saved_room.get("items", room.items))
            room.enemy = saved_room.get("enemy")
            room.locked = bool(saved_room.get("locked", room.locked))
            room.lock_reason = str(saved_room.get("lock_reason", room.lock_reason))
            room.shop_items = dict(saved_room.get("shop_items", room.shop_items))
            room.ai_generated = bool(saved_room.get("ai_generated", room.ai_generated))

        saved_has_exits = any(
            isinstance(saved_room, dict) and "exits" in saved_room
            for saved_room in room_data.values()
        )
        if saved_has_exits:
            for room in self.rooms.values():
                room.exits = {}
            for name, saved_room in room_data.items():
                room = self.rooms.get(name)
                if not room or not isinstance(saved_room, dict):
                    continue
                exits = saved_room.get("exits", {})
                if not isinstance(exits, dict):
                    continue
                for direction, target_name in exits.items():
                    target = self.rooms.get(str(target_name))
                    if direction in DIRECTIONS and target:
                        room.exits[direction] = target

        self.player = Player(
            current_room=self.rooms.get(current_room_name, self.rooms["Entrance"]),
            hp=int(player_data.get("hp", 20)),
            max_hp=int(player_data.get("max_hp", 20)),
            inventory=list(player_data.get("inventory", [])),
            gold=int(player_data.get("gold", 0)),
        )
        print(f"Loaded saved game from {SAVE_FILE}.")
        return True

    def new_game(self) -> None:
        """Reset the dungeon to a fresh run."""
        self.rooms = self._build_world()
        self.player = Player(current_room=self.rooms["Entrance"])
        print("Started a new game. Use 'save' to overwrite any existing save.")
        self.look()

    def search(self) -> None:
        room = self.player.current_room
        print("You search carefully for danger, tracks, and hidden supplies.")

        if not room.items and random.random() < 0.2:
            room.items.append("healing herb")
            print("You uncover a hidden healing herb.")

        if not room.enemy and random.random() < 0.25:
            room.enemy = "wandering rat"
            print("A wandering rat appears!")

    def rest(self) -> None:
        room = self.player.current_room
        if room.enemy:
            print("You can't rest while an enemy is here!")
            return

        healed = random.randint(2, 5)
        old_hp = self.player.hp
        self.player.hp = min(self.player.max_hp, self.player.hp + healed)
        print(f"You rest for a moment. HP: {old_hp} -> {self.player.hp}")

    def stats(self) -> None:
        print(f"HP: {self.player.hp}/{self.player.max_hp}")
        print(f"Gold: {self.player.gold}")
        weapon = "iron sword" if "iron sword" in self.player.inventory else "none"
        shield = "wooden shield" if "wooden shield" in self.player.inventory else "none"
        print(f"Weapon: {weapon}")
        print(f"Shield: {shield}")

    def show_map(self) -> None:
        print("\nDungeon map:")
        print("  [Entrance] --north--> [Hall] --north--> [Shrine] --east--> [Vault]")
        print("                        |")
        print("                        +--east--> [Armory]")
        print("                        |")
        print("                        +--west--> [Merchant Nook]")
        print("  AI-generated rooms branch from wherever you type 'explore'.")

    def show_inventory(self) -> None:
        print(f"HP: {self.player.hp}/{self.player.max_hp} | Gold: {self.player.gold}")
        if not self.player.inventory:
            print("Inventory: empty")
            return
        print("Inventory:", ", ".join(self.player.inventory))


def choose_game() -> DungeonGame:
    """Create a game and optionally restore progress before the loop starts."""
    game = DungeonGame()
    if not SAVE_FILE.exists():
        return game

    print(f"Saved progress found at {SAVE_FILE}.")
    choice = input("Continue saved game? (c = continue, n = new): ").strip().lower()
    if choice in {"c", "continue", "y", "yes", "load"}:
        game.load_game()
    else:
        print("Starting a fresh game. Your old save remains until you use 'save'.")
    return game


if __name__ == "__main__":
    choose_game().start()
