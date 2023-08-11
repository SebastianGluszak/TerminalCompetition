import gamelib
import random
from sys import maxsize
import json
# import math
# import warnings

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

        # Additional turrets reinforce our defense.
        self.non_reactive_turret_locations = [[1, 12], [23, 11], [22, 11], [25, 11]]
        self.reactive_turret_locations = [[]]

        # Supports reinforce our offense. They're currently non-reactive and prioritize higher Y-position for
        # potential upgrading. I would suppose we won't have reactive supports.
        self.support_locations = [[21, 10], [22, 10], [20, 9], [21, 9], [7, 8], [8, 8], [9, 8], [10, 8],
                                  [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8],
                                  [19, 8]]

        # The demolisher_charge is one of our Zerg rush strategies. It should be used when the enemy has some defense
        # while we don't have numerous supports. We'll stack demolishers on one point to achieve maximal efficiency.
        self.demolisher_assembly_point = [[4, 9]]

        # The scout_charge is one of our Zerg rush strategies. It should be used when we have lots of supports,
        # or when we are at a huge advantage, or if we find a huge breach in enemy's defense.
        self.scout_assembly_point = [[4, 9]]

        # This might be useful in the future.
        # self.helper_map = gamelib.game_map.GameMap(self.config)
        # self.friendly_edges = self.helper_map.get_edge_locations(
        #     self.helper_map.BOTTOM_LEFT) + self.helper_map.get_edge_locations(self.helper_map.BOTTOM_RIGHT)

        # We record the locations we and the enemy scored on (on action frame).
        self.locations_we_scored_on = []
        self.locations_enemy_scored_on = []

        # We record where enemy tends to stack their mobile units (on action frame).
        self.enemy_assembly_points = []

        # We record structure counts for analysis.
        self.last_turn_structure_count = {}


    # We do nothing in this function.
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

    # For each turn, we try to estimate our situation, and act accordingly.
    def on_turn(self, turn_state):
        # Boilerplate for on_turn
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        # User defined on_turn behavior
        self.last_turn_structure_count=self.count_all_structures(game_state)
        self.update_situation(game_state)
        self.situation_based_strategy(game_state, self.situation)
        game_state.submit_turn()

    # Tracks breaches and enemy assembly points.
    def on_action_frame(self, action_frame_game_state):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(action_frame_game_state)
        # Check if opponent has deployed any mobile units (frame 0)
        if state["turnInfo"][2] == 0:
            p2_units = state["p2Units"]
            scouts = p2_units[3]
            demolishers = p2_units[4]
            interceptors = p2_units[5]
            for scout in scouts:
                location = [scout[0], scout[1]]
                self.enemy_assembly_points.append(location)
            for demolisher in demolishers:
                location = [demolisher[0], demolisher[1]]
                self.enemy_assembly_points.append(location)
            for interceptor in interceptors:
                location = [interceptor[0], interceptor[1]]
                self.enemy_assembly_points.append(location)

        # Check for breaches
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if unit_owner_self:
                self.locations_we_scored_on.append(location)
            else:
                self.locations_enemy_scored_on.append(location)

    # Situation is estimated based on health, structures, and resources. It uses a scoring system.
    # Right now it's basically random numbers.
    def update_situation(self, game_state):
        score = 0
        score += 10 * (game_state.my_health - game_state.enemy_health)
        score += 5 * (self.count_structure(self.last_turn_structure_count,SUPPORT, 0) - self.count_structure(self.last_turn_structure_count,SUPPORT, 1))
        score += 3 * (self.count_structure(self.last_turn_structure_count,TURRET, 0) - self.count_structure(self.last_turn_structure_count,TURRET, 1))
        score += 0.5 * (self.count_structure(self.last_turn_structure_count,TURRET, 0) - self.count_structure(self.last_turn_structure_count,TURRET, 1))
        score += 1 * (game_state.get_resource(MP, 0) + game_state.get_resource(SP, 0)
                      - game_state.get_resource(MP, 1) - game_state.get_resource(SP, 1))
        if score > 30:
            self.situation = ADVANTAGE
        elif score < -30:
            self.situation = DISADVANTAGE
        else:
            self.situation = BALANCE

    # This calls corresponding strategies. It's called each turn.
    def situation_based_strategy(self, game_state, situation):
        if situation == ADVANTAGE:
            self.advantage_strategy(game_state)
        elif situation == DISADVANTAGE:
            self.disadvantage_strategy(game_state)
        else:
            self.balance_strategy(game_state)

    def advantage_strategy(self, game_state):
        # Vanilla idea: first make sure base is good, then build a few turrets and supports, then assemble troops and
        # prepare for an attack. If we're rich in structure points, then build more supports first and then turrets.
        self.build_base(game_state)
        self.build_a_few_turrets(game_state)
        self.build_a_few_supports(game_state)
        self.build_more_supports(game_state)
        self.build_more_turrets(game_state)
        # We might also want to attack only if we have at least one support.
        if game_state.number_affordable(DEMOLISHER) >= 4:
            self.demolisher_charge(game_state)

    def balance_strategy(self, game_state):
        pass

    # We should prioritize improving advantage & balance strategies over implementing disadvantage_strategy, because we
    # might not fall behind at all if we do well in other situations.
    def disadvantage_strategy(self, game_state):
        pass

    ########################################################################################
    # Below this line are specific helper functions that are called by our strategies.
    ########################################################################################

    def build_base(self, game_state):
        if game_state.turn_number == 0:
            game_state.attempt_spawn(WALL, self.base_wall_locations)
        game_state.attempt_spawn(TURRET, self.base_turret_locations)
        game_state.attempt_upgrade(self.base_turret_locations)
        game_state.attempt_spawn(WALL, self.base_wall_locations)

    def build_a_few_turrets(self, game_state):
        pass

    def build_a_few_supports(self, game_state):
        pass

    def build_more_supports(self, game_state):
        for location in self.support_locations:
            if game_state.number_affordable(SUPPORT) < 1:
                break
            if not game_state.contains_stationary_unit(location):
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
            elif not self.is_badly_damaged(game_state, location):
                game_state.attempt_upgrade(location)

    def build_more_turrets(self, game_state):
        game_state.attempt_spawn(TURRET, self.non_reactive_turret_locations)

    def demolisher_charge(self, game_state):
        game_state.attempt_spawn(DEMOLISHER, self.demolisher_assembly_point,
                                 num=game_state.number_affordable(DEMOLISHER))

    def scout_charge(self, game_state):
        game_state.attempt_spawn(SCOUT, self.scout_assembly_point,
                                 num=game_state.number_affordable(SCOUT))

    def count_structure(self, all_structure_count, unit_type, player_index):
        return all_structure_count[player_index][unit_type]

    def count_all_structures(self, game_state):
        """
        Counts the number of each particular structure for each player
        ARGUMENTS:
        self := self
        game_state := game_state
        RETURNS:
        List of structure counts for each player where counts[0] := ours counts[1] := opponent
        """
        counts = [{"WALL": 0, "SUPPORT": 0, "TURRET": 0}, {"WALL": 0, "SUPPORT": 0, "TURRET": 0}]
        for x in range(28):
            for y in range(28):
                location = [x, y]
                if game_state.game_map.in_arena_bounds(location):
                    unit = game_state.contains_stationary_unit(game_state.self, location)
                    counts[unit.player_index][unit.unit_type] += 1 if unit != False else 0
        return counts

    def is_badly_damaged(self, game_state, location):
        # could be different criteria for different structures (maybe it could be a parameter we’ll fine tune)
        return False

    def replace_broken_structures(self):
        # delete the structures badly damaged and under attack (need a way to check under attack or not)
        pass


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
