import unittest
from env.engine import PuertoRicoGame
from configs.constants import Phase, Role, Good, TileType, BuildingType

class TestPuertoRicoGame(unittest.TestCase):

    def setUp(self):
        self.game = PuertoRicoGame(num_players=4)

    def test_setup(self):
        self.assertEqual(len(self.game.players), 4)
        self.assertEqual(self.game.vp_chips, 100)
        self.assertEqual(self.game.colonists_supply, 75)
        self.assertEqual(self.game.colonists_ship, 4)
        
        # Check initial doubloons
        for p in self.game.players:
            self.assertEqual(p.doubloons, 3)
            
        # Check plantations
        gov_idx = self.game.governor_idx
        self.assertEqual(self.game.players[gov_idx].island_board[0].tile_type, TileType.INDIGO_PLANTATION)
        self.assertEqual(self.game.players[(gov_idx + 1) % 4].island_board[0].tile_type, TileType.INDIGO_PLANTATION)
        self.assertEqual(self.game.players[(gov_idx + 2) % 4].island_board[0].tile_type, TileType.CORN_PLANTATION)
        self.assertEqual(self.game.players[(gov_idx + 3) % 4].island_board[0].tile_type, TileType.CORN_PLANTATION)

    def test_start_game(self):
        self.game.start_game()
        self.assertEqual(len(self.game.face_up_plantations), 5)
        self.assertEqual(self.game.current_phase, Phase.END_ROUND)

    def test_role_selection(self):
        self.game.start_game()
        player_idx = self.game.current_player_idx
        self.game.select_role(player_idx, Role.SETTLER)
        
        self.assertEqual(self.game.current_phase, Phase.SETTLER)
        self.assertEqual(self.game.active_role, Role.SETTLER)
        self.assertNotIn(Role.SETTLER, self.game.available_roles)
        self.assertEqual(self.game.active_role_player_idx(), player_idx)

    def test_settler_phase(self):
        self.game.start_game()
        player_idx = self.game.current_player_idx
        
        # Pick Settler
        self.game.select_role(player_idx, Role.SETTLER)
        
        # Take Quarry (Privilege)
        self.game.action_settler(player_idx, tile_choice=-1)
        self.assertEqual(self.game.players[player_idx].island_board[-1].tile_type, TileType.QUARRY)
        
        # Next player takes a face up plantation
        next_player = self.game.current_player_idx
        self.game.action_settler(next_player, tile_choice=0)
        self.assertEqual(len(self.game.players[next_player].island_board), 2)
        
        # Others pass
        for _ in range(2):
            self.game.action_settler(self.game.current_player_idx, tile_choice=-2)
            
        # Phase should end, next player in line to pick role
        self.assertEqual(self.game.current_phase, Phase.END_ROUND)
        self.assertEqual(self.game.current_player_idx, next_player)

class TestPuertoRicoGame2Player(unittest.TestCase):

    def setUp(self):
        self.game = PuertoRicoGame(num_players=2)

    def test_2player_setup(self):
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.vp_chips, 65)
        self.assertEqual(self.game.colonists_supply, 40)
        self.assertEqual(self.game.colonists_ship, 2)
        
        # Check initial doubloons
        for p in self.game.players:
            self.assertEqual(p.doubloons, 3)
            
        # Check plantations
        gov_idx = self.game.governor_idx
        self.assertEqual(self.game.players[gov_idx].island_board[0].tile_type, TileType.INDIGO_PLANTATION)
        self.assertEqual(self.game.players[(gov_idx + 1) % 2].island_board[0].tile_type, TileType.CORN_PLANTATION)

        # Check buildings supply
        self.assertEqual(self.game.building_supply[BuildingType.SMALL_INDIGO_PLANT], 2)
        self.assertEqual(self.game.building_supply[BuildingType.INDIGO_PLANT], 2)
        self.assertEqual(self.game.building_supply[BuildingType.SMALL_MARKET], 1)
        self.assertEqual(self.game.building_supply[BuildingType.GUILDHALL], 1)

    def test_2player_role_selection_rotation(self):
        self.game.start_game()
        
        roles_to_pick = [
            Role.SETTLER, Role.MAYOR, Role.BUILDER,
            Role.CRAFTSMAN, Role.TRADER, Role.CAPTAIN
        ]
        
        gov_idx = self.game.governor_idx
        other_idx = (gov_idx + 1) % 2
        
        # In a 2 player game, picking goes: Gov, Other, Gov, Other, Gov, Other (total 6 roles)
        
        for i, role in enumerate(roles_to_pick):
            expected_player = gov_idx if i % 2 == 0 else other_idx
            self.assertEqual(self.game.current_player_idx, expected_player)
            
            # This player picks a role
            self.game.select_role(expected_player, role)
            
            # They do whatever (just pass to end phase)
            if role == Role.SETTLER:
                self.game.action_settler(expected_player, tile_choice=-2)
                self.game.action_settler((expected_player + 1) % 2, tile_choice=-2)
            elif role == Role.MAYOR:
                # Mayor phase requires sequential placement for both players
                # Player who picked Mayor goes first, then the other
                mayor_picker = expected_player
                other_player = (expected_player + 1) % 2
                
                # 1. Mayor Picker placement loop
                p = self.game.players[mayor_picker]
                self.game._init_mayor_placement(mayor_picker)
                # Place all owned colonists sequentially
                # For simplicity in this test, just place 0 everywhere until run out
                # But wait, we must place if possible.
                # Let's just place 0 everywhere and rely on "Must Place" logic?
                # No, engine raises error if we don't place.
                # Let's just fill island slots 0..N with 1 until run out of colonists
                
                # Since this test just checks rotation, we just need to get through the phase.
                # Loop 24 times for first player
                for _ in range(24):
                    # Check capacity of current slot
                    idx = self.game.mayor_placement_idx
                    p = self.game.players[mayor_picker]
                    capacity = 0
                    if idx < 12: # Island
                        if idx < len(p.island_board) and p.island_board[idx].tile_type != TileType.EMPTY:
                            capacity = 1
                    else: # Building
                        b_idx = idx - 12
                        if b_idx < len(p.city_board) and p.city_board[b_idx].building_type not in (BuildingType.EMPTY, BuildingType.OCCUPIED_SPACE):
                            capacity = BUILDING_DATA[p.city_board[b_idx].building_type][2]
                            
                    amount = 1 if (p.unplaced_colonists > 0 and capacity > 0) else 0
                    self.game.action_mayor_place(mayor_picker, amount)
                    
                # 2. Other Player placement loop
                p = self.game.players[other_player]
                self.game._init_mayor_placement(other_player)
                for _ in range(24):
                    idx = self.game.mayor_placement_idx
                    p = self.game.players[other_player]
                    capacity = 0
                    if idx < 12: # Island
                        if idx < len(p.island_board) and p.island_board[idx].tile_type != TileType.EMPTY:
                            capacity = 1
                    else: # Building
                        b_idx = idx - 12
                        if b_idx < len(p.city_board) and p.city_board[b_idx].building_type not in (BuildingType.EMPTY, BuildingType.OCCUPIED_SPACE):
                            capacity = BUILDING_DATA[p.city_board[b_idx].building_type][2]
                            
                    amount = 1 if (p.unplaced_colonists > 0 and capacity > 0) else 0
                    self.game.action_mayor_place(other_player, amount)

            elif role == Role.BUILDER:
                self.game.action_builder(expected_player, building_choice=None)
                self.game.action_builder((expected_player + 1) % 2, building_choice=None)
            elif role == Role.CRAFTSMAN:
                if self.game.current_phase == Phase.CRAFTSMAN:
                    self.game.action_craftsman(expected_player, privilege_good=None)
            elif role == Role.TRADER:
                self.game.action_trader(expected_player, sell_good=None)
                self.game.action_trader((expected_player + 1) % 2, sell_good=None)
            elif role == Role.CAPTAIN:
                for target_p in self.game.players:
                    for g in Good:
                        target_p.goods[g] = 0
                self.game.action_captain_pass(expected_player)
                self.game.action_captain_pass((expected_player + 1) % 2)
                
                # Captain phase ALWAYS advances to Captain Store phase
                if self.game.current_phase == Phase.CAPTAIN_STORE:
                    self.game.action_captain_store_pass(expected_player)
                    self.game.action_captain_store_pass((expected_player + 1) % 2)
                
            if i < 5:
                # Still END_ROUND (waiting for next role pick)
                self.assertEqual(self.game.current_phase, Phase.END_ROUND)
            else:
                # After 6th role, round ends, governor passes
                self.assertEqual(self.game.current_phase, Phase.END_ROUND)
                self.assertEqual(self.game.governor_idx, other_idx)

if __name__ == '__main__':
    unittest.main()
