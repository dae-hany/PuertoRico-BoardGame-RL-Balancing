import unittest
from env.engine import PuertoRicoGame
from env.pr_env import PuertoRicoEnv
from configs.constants import Phase, Role, BuildingType, TileType, BUILDING_DATA

class TestMayorSequential(unittest.TestCase):
    def test_mayor_sequential_placement(self):
        # Setup
        env = PuertoRicoEnv(num_players=3)
        env.reset()
        game = env.game
        
        # Manually force Mayor Phase
        game.current_phase = Phase.MAYOR
        game.current_player_idx = 0
        game.players[0].unplaced_colonists = 3 # Player has 3 colonists
        
        # Give some buildings
        game.players[0].build_building(BuildingType.SMALL_INDIGO_PLANT) # Cap 1
        game.players[0].build_building(BuildingType.SMALL_MARKET) # Cap 1
        # Has Corn (Cap 1) and Indigo (Cap 1) plantations initially usually
        # Let's ensure island configuration
        game.players[0].island_board = []
        game.players[0].place_plantation(TileType.CORN_PLANTATION) # Slot 0
        game.players[0].place_plantation(TileType.INDIGO_PLANTATION) # Slot 1
        
        # Init placement
        game._init_mayor_placement(0)
        
        # --- Slot 0: Corn (Capacity 1) ---
        # Player has 3 col. Future cap: Indigo(1) + SmIndigo(1) + SmMarket(1) = 3
        # Available(3) - Future(3) = 0. Min place 0. Max place 1.
        # Action 69 (0 place) should be valid.
        mask = env.valid_action_mask()
        self.assertTrue(mask[69]) # 0
        self.assertTrue(mask[70]) # 1
        
        # Agent chooses 0
        env.step(69) 
        self.assertEqual(game.mayor_placement_idx, 1)
        self.assertEqual(game.players[0].unplaced_colonists, 3)
        self.assertFalse(game.players[0].island_board[0].is_occupied)

        # --- Slot 1: Indigo (Capacity 1) ---
        # Player has 3 col. Future cap: SmIndigo(1) + SmMarket(1) = 2.
        # Available(3) - Future(2) = 1. Min place 1. Max place 1.
        # MUST place 1.
        mask = env.valid_action_mask()
        self.assertFalse(mask[69]) # 0 invalid
        self.assertTrue(mask[70])  # 1 valid
        
        # Agent chooses 1
        env.step(70)
        self.assertEqual(game.mayor_placement_idx, 2)
        self.assertEqual(game.players[0].unplaced_colonists, 2)
        self.assertTrue(game.players[0].island_board[1].is_occupied)
        
        # --- Slots 2-11: Empty Island (Capacity 0) ---
        for i in range(2, 12):
            mask = env.valid_action_mask()
            self.assertTrue(mask[69]) # 0 valid
            self.assertFalse(mask[70]) # 1 invalid
            env.step(69)
            
        self.assertEqual(game.mayor_placement_idx, 12)
        
        # --- Slot 12: Small Indigo (Capacity 1) ---
        # Player has 2 col. Future cap: SmMarket(1).
        # Available(2) - Future(1) = 1. Min place 1. Max place 1.
        env.step(70) # Place 1
        self.assertEqual(game.players[0].unplaced_colonists, 1)
        self.assertEqual(game.players[0].city_board[0].colonists, 1)
        
        # --- Slot 13: Small Market (Capacity 1) ---
        # Player has 1 col. Future cap: 0.
        # Available(1) - Future(0) = 1. Min place 1. Max place 1.
        env.step(70) # Place 1
        self.assertEqual(game.players[0].unplaced_colonists, 0)
        self.assertEqual(game.players[0].city_board[1].colonists, 1)
        
        # --- Remaining Slots 14-23 ---
        # Player has 0 col.
        for i in range(14, 24):
            env.step(69) # Place 0
            
        # Turn should advance to next player
        self.assertNotEqual(game.current_player_idx, 0)
        
        print("TestMayorSequential Passed!")

if __name__ == '__main__':
    unittest.main()
