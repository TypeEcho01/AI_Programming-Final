from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
        hall.connect("east", armory)
        hall.connect("north", shrine)
        shrine.connect("east", vault)

        return {room.name: room for room in [entrance, hall, armory, shrine, vault]}

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
            case "search":
                self.search()
            case "rest":
                self.rest()
            case "unlock":
                self.unlock()
            case "map":
                self.show_map()
            case "quit" | "exit":
                print("You leave the dungeon.")
                self.running = False
            case _:
                print("Unknown command. Type 'help' for options.")

    def help(self) -> None:
        print(
            "Commands: help, look, go <direction>, take <item>, drop <item>, "
            "attack, use <item>, unlock, search, map, rest, stats, inventory, quit"
        )

    def look(self) -> None:
        room = self.player.current_room
        print(f"\n== {room.name} ==")
        print(room.description)

        if room.enemy:
            print(f"Enemy present: {room.enemy}")

        if room.items:
            print("You see:", ", ".join(room.items))

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

        if real_name in {"ancient coin", "ruby idol"}:
            value = 5 if real_name == "ancient coin" else 20
            self.player.gold += value
            print(f"You pocket the {real_name} and gain {value} gold.")
            return

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
            print(f"You defeated the {room.enemy}!")
            room.enemy = None
            self.player.gold += 3
            print("You collect 3 gold from the remains.")
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

    def search(self) -> None:
        room = self.player.current_room
        found_gold = random.randint(1, 4)
        self.player.gold += found_gold
        print(f"You search carefully and find {found_gold} gold.")

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

    def show_inventory(self) -> None:
        print(f"HP: {self.player.hp}/{self.player.max_hp} | Gold: {self.player.gold}")
        if not self.player.inventory:
            print("Inventory: empty")
            return
        print("Inventory:", ", ".join(self.player.inventory))


if __name__ == "__main__":
    DungeonGame().start()
