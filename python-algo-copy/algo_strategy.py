import gamelib
import random
from sys import maxsize

# import math
# import warnings
# import json

global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
global ADVANTAGE, DISADVANTAGE, BALANCE


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        # Boilerplate for an algo.
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        # Below are user-defined attributes.

        # We try to implement a situation-based strategy. Situation is estimated based on health, structures,
        # and resources. On a high level, our algo tends to be more aggressive when we're at an advantage and more
        # cautious otherwise.
        global ADVANTAGE, DISADVANTAGE, BALANCE
        ADVANTAGE, DISADVANTAGE, BALANCE = 1, -1, 0
        self.situation = ADVANTAGE  # Will change to BALANCE after we implement the BALANCE strategy.

        # Base walls and base turrets are what we try to maintain all the time.
        # The base walls direct our mobile units to the enemy's right flank.
        # The base turrets focuses on our own right flank.
        self.base_wall_locations = [[0, 13], [1, 13], [23, 13], [26, 13], [27, 13], [2, 12], [3, 12], [22, 12],
                                    [25, 12],
                                    [4, 11], [21, 11], [5, 10], [20, 10], [6, 9], [7, 9], [8, 9], [9, 9],
                                    [10, 9], [11, 9],
                                    [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9]]
        self.base_turret_locations = [[23, 12], [2, 11]]

        # Additional turrets reinforce our defense. They're currently non-reactive.
        self.additional_turret_locations = [[1, 12], [23, 11], [22, 11], [25, 11]]

        # Supports reinforce our offense. They're currently non-reactive and prioritize higher Y-position for
        # potential upgrading.
        self.support_locations = [[21, 10], [22, 10], [20, 9], [21, 9], [7, 8], [8, 8], [9, 8], [10, 8],
                                  [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8],
                                  [19, 8]]

        # The demolisher_charge is one of our Zerg rush strategies. It should be used when the enemy has some defense
        # while we don't have numerous supports. We'll stack demolishers on one point to achieve maximal efficiency.
        self.demolisher_assembly_point = [[4, 9]]

        # The scout_charge is one of our Zerg rush strategies. It should be used when we have lots of supports,
        # or when we are at a huge advantage, or if we found a huge breach in enemy's defense.
        self.scout_assembly_point = [[4, 9]]

        # self.helper_map = gamelib.game_map.GameMap(self.config)
        # self.friendly_edges = self.helper_map.get_edge_locations(
        #     self.helper_map.BOTTOM_LEFT) + self.helper_map.get_edge_locations(self.helper_map.BOTTOM_RIGHT)

        # We record the locations we and the enemy scored on (on action frame).
        self.locations_we_scored_on = []
        self.locations_enemy_scored_on = []

        # We record where enemy tends to stack their mobile units (on action frame).
        self.enemy_assembly_points = []

    def on_game_start(self, config):
        # Boilerplate for game_start.
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

        # User-defined initial setup. (I don't think there has to be any for now.)
        pass

    def on_turn(self, turn_state):
        # Boilerplate for on_turn
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        # User defined on_turn behavior
        self.update_situation(game_state)
        self.situation_based_strategy(game_state, self.situation)
        game_state.submit_turn()

    # Situation is estimated based on health, structures, and resources. It uses a scoring system.
    def update_situation(self, game_state):
        score = 0
        score += 10 * (game_state.my_health - game_state.enemy_health)
        score += 5 * (self.count_structure(SUPPORT, 0) - self.count_structure(SUPPORT, 1))
        score += 3 * (self.count_structure(TURRET, 0) - self.count_structure(TURRET, 1))
        score += 0.5 * (self.count_structure(TURRET, 0) - self.count_structure(TURRET, 1))
        score += 1 * (game_state.get_resource(MP, 0) + game_state.get_resource(SP, 0)
                      - game_state.get_resource(MP, 1) - game_state.get_resource(SP, 1))
        if score > 30:
            self.situation = ADVANTAGE
        elif score < -30:
            self.situation = DISADVANTAGE
        else:
            self.situation = BALANCE

    def situation_based_strategy(self, game_state, situation):
        if situation == ADVANTAGE:
            self.advantage_strategy(game_state)
        elif situation == DISADVANTAGE:
            self.disadvantage_strategy(game_state)
        else:
            self.balance_strategy(game_state)

    def advantage_strategy(self, game_state):
        self.build_base(game_state)
        self.build_defense(game_state)
        self.build_supports(game_state)
        if game_state.number_affordable(DEMOLISHER) >= 4:
            self.demolisher_charge(game_state)

    def balance_strategy(self, game_state):
        pass

    # We should prioritize improving advantage & balance strategies over implementing disadvantage_strategy, because we
    # might not fall behind at all if we do well in other situations.
    def disadvantage_strategy(self, game_state):
        pass

    def demolisher_charge(self, game_state):
        game_state.attempt_spawn(DEMOLISHER, self.demolisher_assembly_point,
                                 num=game_state.number_affordable(DEMOLISHER))

    def build_supports(self, game_state):
        for location in self.support_locations:
            if game_state.number_affordable(SUPPORT) < 1:
                break
            if not game_state.contains_stationary_unit(location):
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
            elif not self.is_badly_damaged(game_state, location):
                game_state.attempt_upgrade(location)

    def build_defense(self, game_state):
        game_state.attempt_spawn(TURRET, self.additional_turret_locations)

    def build_base(self, game_state):
        if game_state.turn_number == 0:
            game_state.attempt_spawn(WALL, self.base_wall_locations)
        game_state.attempt_spawn(TURRET, self.base_turret_locations)
        game_state.attempt_upgrade(self.base_turret_locations)
        game_state.attempt_spawn(WALL, self.base_wall_locations)

    def is_badly_damaged(self, game_state, location):
        return False

    def count_structure(self, unit_type, player_index):
        return 0


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
