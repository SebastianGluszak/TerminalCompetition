import gamelib
import random
import math
import warnings
from sys import maxsize
import json

global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
global ADVANTAGE, DISADVANTAGE, BALANCE


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        # Below are user-defined attributes.
        global ADVANTAGE, DISADVANTAGE, BALANCE
        ADVANTAGE, DISADVANTAGE, BALANCE = 1, -1, 0
        self.situation = ADVANTAGE
        self.base_wall_locations = [[0, 13], [1, 13], [23, 13], [26, 13], [27, 13], [2, 12], [3, 12], [22, 12],
                                    [25, 12],
                                    [4, 11], [21, 11], [5, 10], [20, 10], [6, 9], [7, 9], [8, 9], [9, 9],
                                    [10, 9], [11, 9],
                                    [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9]]
        self.base_turret_locations = [[23, 12], [2, 11]]
        self.preferred_turret_locations = [[23, 12], [26, 12], [1, 12], [23, 11], [22, 11], [25, 11]]
        self.preferred_support_locations = [[21, 10], [22, 10], [20, 9], [21, 9], [7, 8], [8, 8], [9, 8], [10, 8],
                                            [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8],
                                            [19, 8]]
        self.demolisher_assembly_point = [[4, 9]]
        # self.helper_map = gamelib.game_map.GameMap(self.config)
        # self.friendly_edges = self.helper_map.get_edge_locations(
        #     self.helper_map.BOTTOM_LEFT) + self.helper_map.get_edge_locations(self.helper_map.BOTTOM_RIGHT)

    def on_game_start(self, config):
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

        # Initial setup
        global ADVANTAGE, DISADVANTAGE, BALANCE
        ADVANTAGE, DISADVANTAGE, BALANCE = 1, -1, 0

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        # Situation might depend on action frames beyond game_state.
        self.update_situation()
        self.situation_based_strategy(game_state)
        game_state.submit_turn()

    def situation_based_strategy(self, game_state):
        self.build_base(game_state)
        if self.situation == ADVANTAGE:
            self.build_defense(game_state)
            self.build_supports(game_state)
            if game_state.number_affordable(DEMOLISHER) >= 4:
                self.demolisher_charge(game_state)
        elif self.situation == DISADVANTAGE:
            # Haven't implemented DISADVANTAGE strategy.
            self.build_defense(game_state)
            self.build_supports(game_state)
            if game_state.number_affordable(DEMOLISHER) >= 4:
                self.demolisher_charge(game_state)
        else:
            # Haven't implemented BALANCE strategy.
            self.build_defense(game_state)
            self.build_supports(game_state)
            if game_state.number_affordable(DEMOLISHER) >= 4:
                self.demolisher_charge(game_state)

    # def predict_enemy_attack_time(self,game_state):
    #     pass

    def demolisher_charge(self, game_state):
        game_state.attempt_spawn(DEMOLISHER, self.demolisher_assembly_point,
                                 num=game_state.number_affordable(DEMOLISHER))

    def update_situation(self):
        pass

    def build_supports(self, game_state):
        for location in self.preferred_support_locations:
            if game_state.number_affordable(SUPPORT) < 1:
                break
            if not game_state.contains_stationary_unit(location):
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
            elif not self.is_badly_damaged(game_state, location):
                game_state.attempt_upgrade(location)

    def build_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.preferred_turret_locations)

    def is_badly_damaged(self, game_state, location):
        return False

    def build_base(self, game_state):
        if game_state.turn_number == 0:
            game_state.attempt_spawn(WALL, self.base_wall_locations)
        game_state.attempt_spawn(TURRET, self.base_turret_locations)
        game_state.attempt_upgrade(self.base_turret_locations)
        game_state.attempt_spawn(WALL, self.base_wall_locations)

    def count_structure(self, unit_type, player_index):
        return 0


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
