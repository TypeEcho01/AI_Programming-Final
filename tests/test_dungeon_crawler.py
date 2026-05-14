import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import dungeon_crawler
from dungeon_crawler import DungeonGame, Room


class DungeonCrawlerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_save_file = dungeon_crawler.SAVE_FILE
        dungeon_crawler.SAVE_FILE = Path(self.temp_dir.name) / "dungeon_save.json"

    def tearDown(self):
        dungeon_crawler.SAVE_FILE = self.original_save_file
        self.temp_dir.cleanup()

    def run_silently(self, func, *args, **kwargs):
        with redirect_stdout(io.StringIO()):
            return func(*args, **kwargs)

    def test_room_connections_are_bidirectional(self):
        entrance = Room("Entrance", "Start")
        hall = Room("Hall", "A hallway")

        entrance.connect("north", hall)

        self.assertIs(entrance.exits["north"], hall)
        self.assertIs(hall.exits["south"], entrance)

    def test_take_and_drop_moves_item_between_room_and_inventory(self):
        game = DungeonGame()

        self.run_silently(game.take, "torch")
        self.assertIn("torch", game.player.inventory)
        self.assertNotIn("torch", game.player.current_room.items)

        self.run_silently(game.drop, "torch")
        self.assertNotIn("torch", game.player.inventory)
        self.assertIn("torch", game.player.current_room.items)

    def test_buy_spends_gold_and_adds_shop_item_to_inventory(self):
        game = DungeonGame()
        game.player.current_room = game.rooms["Merchant Nook"]
        game.player.gold = 9

        self.run_silently(game.buy, "small potion")

        self.assertEqual(game.player.gold, 0)
        self.assertIn("small potion", game.player.inventory)

    def test_buy_without_enough_gold_does_not_add_item(self):
        game = DungeonGame()
        game.player.current_room = game.rooms["Merchant Nook"]
        game.player.gold = 4

        self.run_silently(game.buy, "healing herb")

        self.assertEqual(game.player.gold, 4)
        self.assertNotIn("healing herb", game.player.inventory)

    def test_attack_defeats_enemy_and_awards_enemy_gold(self):
        game = DungeonGame()
        game.player.current_room = game.rooms["Shrine"]

        with patch("random.randint", side_effect=[8, 1]):
            self.run_silently(game.attack)

        self.assertIsNone(game.rooms["Shrine"].enemy)
        self.assertEqual(game.player.gold, dungeon_crawler.ENEMY_GOLD_REWARDS["cult acolyte"])

    def test_throwing_dagger_defeats_enemy_and_awards_gold(self):
        game = DungeonGame()
        game.player.current_room = game.rooms["Shrine"]
        game.player.inventory.append("throwing dagger")

        self.run_silently(game.use_item, "throwing dagger")

        self.assertNotIn("throwing dagger", game.player.inventory)
        self.assertIsNone(game.rooms["Shrine"].enemy)
        self.assertEqual(game.player.gold, dungeon_crawler.ENEMY_GOLD_REWARDS["cult acolyte"])

    def test_ai_room_response_is_sanitized_to_allowed_values(self):
        game = DungeonGame()
        raw_room = {
            "name": "A" * 100,
            "description": "B" * 500,
            "items": ["small potion", "forbidden orb", "torch"],
            "enemy": "dragon",
        }

        room_data = game._coerce_ai_room_data(raw_room)

        self.assertEqual(len(room_data["name"]), 40)
        self.assertEqual(len(room_data["description"]), 240)
        self.assertEqual(room_data["items"], ["small potion", "torch"])
        self.assertIsNone(room_data["enemy"])

    def test_extract_response_text_supports_responses_api_output_shape(self):
        game = DungeonGame()
        response_data = {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "{\"name\":"},
                        {"type": "output_text", "text": "\"Test Room\"}"},
                    ]
                }
            ]
        }

        self.assertEqual(game._extract_response_text(response_data), '{"name":"Test Room"}')

    def test_strip_json_fence_removes_markdown_fence(self):
        game = DungeonGame()

        stripped = game._strip_json_fence('```json\n{"name": "Room"}\n```')

        self.assertEqual(stripped, '{"name": "Room"}')

    def test_generate_ai_room_uses_request_data_and_connects_new_room(self):
        game = DungeonGame()
        game._request_ai_room_data = lambda room, direction: {
            "name": "Crystal Den",
            "description": "A room made from generated crystal.",
            "items": ["torch"],
            "enemy": "wandering rat",
        }

        self.run_silently(game.generate_ai_room)

        self.assertIn("Crystal Den", game.rooms)
        self.assertTrue(game.rooms["Crystal Den"].ai_generated)
        self.assertIs(game.player.current_room, game.rooms["Crystal Den"])
        self.assertIn("torch", game.player.current_room.items)
        self.assertTrue(
            any(room.name == "Entrance" for room in game.player.current_room.exits.values())
        )

    def test_save_and_load_restores_generated_room_and_exits(self):
        game = DungeonGame()
        game._request_ai_room_data = lambda room, direction: {
            "name": "AI Crystal Den",
            "description": "A glittering room generated during the test.",
            "items": ["torch"],
            "enemy": "wandering rat",
        }
        self.run_silently(game.generate_ai_room)
        self.run_silently(game.save_game)

        loaded = DungeonGame()
        self.assertTrue(self.run_silently(loaded.load_game))

        self.assertIn("AI Crystal Den", loaded.rooms)
        loaded_room = loaded.rooms["AI Crystal Den"]
        self.assertTrue(loaded_room.ai_generated)
        self.assertEqual(loaded.player.current_room.name, "AI Crystal Den")
        self.assertTrue(any(room.name == "Entrance" for room in loaded_room.exits.values()))

    def test_load_returns_false_when_save_file_is_missing(self):
        game = DungeonGame()

        self.assertFalse(self.run_silently(game.load_game))


if __name__ == "__main__":
    unittest.main()
