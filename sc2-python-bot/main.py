import os
import random

from typing import Optional
from library import *


class MyAgent(IDABot):
    def __init__(self):
        IDABot.__init__(self)
        self.need_more_supply = False
        self.sought_unit_counts = {}
        self.unit_counter = {}
        self.amount_training = {}
        self.game_ticker = 0
        self.worker_dict = {}
        self.combat_dict = {}
        self.count_bases = 0
        self.count_workers = 0
        self.count_barracks = 0
        self.count_bunkers = 0
        self.count_combat_units = 0
        self.count_refineries = 0
        self.count_depots = 0
        self.count_factories = 0
        self.count_engineering_bays = 0
        self.count_starports = 0
        self.my_units = []
        self.my_bases = []
        self.my_bunkers = {}
        self.my_refineries = {}
        self.attack_points = []
        self.my_minerals = {}  # self.my_minerals[base_id] = list of all minerals connected to that base
        self.closest_chokes = [Point2D(116, 44)]
        self.supply_depot_positions = [Point2DI(43, 149)]
        self.barracks_positions = [Point2DI(33, 33)]
        self.siege_chokes = []
        self.standby_rally_point = Point2D(116, 44)
        self.scouting_points = [Point2D(60, 126), Point2D(28, 109), Point2D(28, 134), Point2D(29, 80),
                                Point2D(61, 94), Point2D(85, 112), Point2D(91, 137), Point2D(124, 135),
                                Point2D(123, 86), Point2D(89, 72), Point2D(66, 55), Point2D(28, 32),
                                Point2D(60, 31), Point2D(90, 40), Point2D(124, 57), Point2D(122, 31)]
        self.scout_counter = 0
        self.enemy_bases = []
        self.keep_attacking = False


    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        self.my_units = sorted(self.get_my_units(), key=lambda unit: unit.id)
        self.manage_command_centers()
        self.print_unit_overview()
        self.get_mineral_list()
        self.get_enemy_bases()
        self.count_things()
        self.set_my_bunkers()
        self.set_my_refineries()
        self.get_worker_dict()
        self.set_combat_dict()
        if self.game_ticker == 0:
            self.set_choke_points()
        elif self.game_ticker % 2 == 0:
            self.count_units()
            self.execute_combat_jobs()
        self.print_debug()
        if self.game_ticker % 2 == 0:
            self.train_requests()
        if self.game_ticker % 5 == 0:
            self.build_refineries()
            self.build_depots()
            self.build_barracks()
            self.build_bunkers()
            self.build_factory()
            self.build_factory_tech_lab()
            self.build_barracks_tech_lab()
            #self.build_engineering_bay()
            #self.build_starport()
            #self.build_starport_tech_lab()
            self.request_workers()
            self.request_marines()
            self.request_tanks()
            self.request_marauders()
            #self.request_medivacs()
            self.build_expansion()
        self.execute_worker_jobs()
        self.game_ticker += 1

    # Ramp south: (115, 46) - (115, 43) - (118, 43)
    # Ramp north: (32, 124) - (35, 125) - (36, 121)
    # Expo 1 choke north: (44, 99)
    # Bunker 1 north: (34,112)
    # Ramp Expo South (116, 54)
    # Ramp Expo North (34, 114)

    # Fusion Core South: (128, 20)
    # Fusion Core North: (22, 147)

    # Expo 1 choke south: (107, 67)
    # Expo 2 choke north: (66, 117)
    # Expo 2 choke south: (84, 50)
    # Expo 3 choke south: (76, 85)
    # Expo 3 choke north: (76, 85) Bygg ej bunker här
    # Expo 4 choke south: (56, 76)
    # Expo 4 choke north: (93, 99)
    # Expo 5 choke south: (122, 101)
    # Expo 5 choke north: (29, 66)

    #Sigetank pos 1 north :(39, 120)
    #Sigetank pos 2 north :(41, 96)
    #Sigetank pos 3 north :(66, 117)
    #Sigetank pos 4 north :(85, 107)
    #Sigetank pos 1 south :(113, 47)
    #Sigetank pos 2 south :(112, 73)
    #Sigetank pos 3 south :(84, 53)
    #Sigetank pos 4 south :(67, 60)

    #Scout pos 1 south:(60, 126)
    #Scout pos 2 south:(28, 109)
    #Scout pos 3 south:(28, 134)
    #Scout pos 4 south:(29, 80)
    # Scout pos 5 south:(61, 94)
    # Scout pos 6 south:(85, 112)
    # Scout pos 7 south:(91, 137)
    # Scout pos 8 south:(124, 135)
    # Scout pos 9 south:(123, 86)
    # Scout pos 10 south:(89, 72)
    # Scout pos 11 south:(66, 55)
    # Scout pos 12 south:(28, 32)
    # Scout pos 13 south:(60, 31)
    # Scout pos 14 south:(90, 40)
    # Scout pos 15 south:(124, 57)
    # Scout pos 16 south:(122, 31)

    # Scout pos 1 north:(122, 31)
    # Scout pos 2 north:(124, 57)
    # Scout pos 3 north:(90, 40)
    # Scout pos 4 north:(60, 31)
    # Scout pos 5 north:(28, 32)
    # Scout pos 6 north:(66, 55)
    # Scout pos 7 north:(89, 72)
    # Scout pos 8 north:(123, 86)
    # Scout pos 9 north:(124, 135)
    # Scout pos 10 north:(91, 137)
    # Scout pos 11 north:(85, 112)
    # Scout pos 12 north:(61, 94)
    # Scout pos 13 north:(29, 80)
    # Scout pos 14 north:(28, 134)
    # Scout pos 15 north:(28, 109)
    # Scout pos 16 north:(60, 126)

    def print_debug(self):
        my_workers = list(self.worker_dict.keys())
        for index, unit in enumerate(my_workers):
            if unit.unit_type.is_worker:
                job = self.worker_dict[unit][0]
                if job == self.GATHERING_MINERALS:
                    debug_string = "<{}: {}>".format(job, unit.position)
                    self.map_tools.draw_text(unit.position, debug_string, Color.TEAL)
                elif job == self.COLLECTING_GAS:
                    debug_string = "<{}>".format(job)
                    self.map_tools.draw_text(unit.position, debug_string, Color.GREEN)
                elif job == self.CONSTRUCTING:
                    debug_string = "<{} {}>".format(job, str(self.worker_dict[unit][1]))
                    self.map_tools.draw_text(unit.position, debug_string, Color.YELLOW)
                elif job == self.SCOUT:
                    debug_string = "<{} {}>".format(job, str(self.worker_dict[unit][1]))
                    self.map_tools.draw_text(unit.position, debug_string, Color.PURPLE)
        for combat_unit in self.combat_dict:
            job = self.combat_dict[combat_unit]
            debug_string = "<{} {}>".format(job[0], job[1])
            self.map_tools.draw_text(combat_unit.position, debug_string, Color.RED)

    def set_my_bunkers(self):
        bunkers = [unit for unit in self.my_units if unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BUNKER, self)]
        old_bunkers = []
        for old_index in list(self.my_bunkers.keys()):
            if not self.my_bunkers[old_index].is_alive:
                del self.my_bunkers[old_index]
            else:
                old_bunkers.append(self.my_bunkers[old_index])
        for bunker_index in range(self.count_bunkers):
            if bunker_index not in self.my_bunkers:
                for bunker in bunkers:
                    if bunker not in old_bunkers:
                        self.my_bunkers[bunker_index] = bunker
                        break

    def set_my_refineries(self):
        refineries = [unit for unit in self.my_units if unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)]
        old_refineries = []
        for old_index in list(self.my_refineries.keys()):
            if not self.my_refineries[old_index].is_alive:
                del self.my_refineries[old_index]
            else:
                old_refineries.append(self.my_refineries[old_index])
        for refinery_index in range(self.count_refineries):
            if refinery_index not in self.my_refineries:
                for refinery in refineries:
                    if refinery not in old_refineries:
                        self.my_refineries[refinery_index] = refinery

    def print_unit_overview(self):
        count_miners = self.count_worker_job(self.GATHERING_MINERALS)
        count_gas_collectors = self.count_worker_job(self.COLLECTING_GAS)
        count_builders = self.count_worker_job(self.CONSTRUCTING)
        count_scouts = self.count_worker_job(self.SCOUT)
        count_choke_defenders = self.count_combat_job(self.DEFEND_CHOKE)
        count_bunker_bois = self.count_combat_job(self.DEFEND_BUNKER)
        count_standby = self.count_combat_job(self.STANDBY)
        count_attackers = self.count_combat_job(self.ATTACKING)
        overview_string = " Unit assignments \n" \
                          " ---------------- \n" \
                          " Miners:           {} \n" \
                          " Gas Collectors:   {} \n" \
                          " Builders:         {} \n" \
                          " Scouts:           {} \n" \
                          " Choke Defenders:  {} \n" \
                          " Bunker Defenders: {} \n" \
                          " Standby Units:    {} \n" \
                          " Attacking Units:  {}".format(count_miners,
                                                                                      count_gas_collectors,
                                                                                      count_builders,
                                                                                      count_scouts,
                                                                                      count_choke_defenders,
                                                                                      count_bunker_bois,
                                                                                      count_standby,
                                                                                      count_attackers)
        self.map_tools.draw_text_screen(0.005, 0.005, overview_string, Color.WHITE)

    def get_mineral_list(self):
        for index, base in enumerate(self.my_bases):
            self.my_minerals[index] = self.get_mineral_fields(base)

    def manage_command_centers(self):
        command_centers = self.get_my_producers(UnitType(UNIT_TYPEID.TERRAN_SCV, self))
        base_locations = self.base_location_manager.get_occupied_base_locations(PLAYER_SELF)
        for base in self.my_bases:
            contains_cc = False
            for command_center in command_centers:
                if base.contains_position(command_center.position):
                    contains_cc = True
            if not contains_cc:
                self.my_bases.remove(base)

        for command_center in command_centers:
            command_center.right_click(command_center)
            if command_center.is_completed:
                for base in base_locations:
                    if base.contains_position(command_center.position) and base not in self.my_bases:
                        self.my_bases.append(base)



    def get_starting_base(self):
        return self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)

    def get_enemy_bases(self):
        self.enemy_bases = list(self.base_location_manager.get_occupied_base_locations(PLAYER_ENEMY))
        if not self.enemy_bases:
            self.enemy_bases = [self.base_location_manager.get_player_starting_base_location(PLAYER_ENEMY)]

    def get_my_workers(self):
        workers = []
        for unit in self.my_units:  # type: Unit
            if unit.unit_type.is_worker:
                workers.append(unit)

        return workers

    def set_combat_dict(self):
        old_units = list(self.combat_dict.keys())
        for combat_unit in old_units:
            if not combat_unit.is_alive:
                self.combat_dict.pop(combat_unit)
            elif self.combat_dict[combat_unit][0] == self.STANDBY:
                self.combat_dict[combat_unit] = self.get_combat_job(combat_unit.unit_type)
        new_combat_units = [unit for unit in self.my_units \
                if unit.unit_type.is_combat_unit and unit not in self.combat_dict]
        for new_unit in new_combat_units:
            self.combat_dict[new_unit] = self.get_combat_job(new_unit.unit_type)

        start_attacking = (self.count_combat_job((self.STANDBY, 0), UnitType(UNIT_TYPEID.TERRAN_MARINE, self)) >= 12 \
                           and self.count_combat_job((self.STANDBY, 0), UnitType(UNIT_TYPEID.TERRAN_MARAUDER, self)) >= 6)
        self.keep_attacking = (self.count_combat_job(self.ATTACKING)) > 15
        if start_attacking:
            self.init_attack_points()
        if self.keep_attacking or start_attacking:
            standby_units = [unit for unit in self.combat_dict if self.combat_dict[unit][0] == self.STANDBY]
            for unit in standby_units:
                self.combat_dict[unit] = (self.ATTACKING, 0)

    DEFEND_CHOKE = "defending choke"
    DEFEND_BUNKER = "defending bunker"
    STANDBY = "standby"
    ATTACKING = "Attacking"

    def get_combat_job(self, unit_type):
        if unit_type == UnitType(UNIT_TYPEID.TERRAN_MARINE, self):
            for bunker_index in range(self.count_bunkers):
                job = (self.DEFEND_BUNKER, bunker_index)
                if self.count_combat_job(job, unit_type) < 4:
                    return job
            for base_index, base in enumerate(self.my_bases):
                job = (self.DEFEND_CHOKE, base_index)
                if self.count_combat_job(job, unit_type) < 4:
                    return job
        if unit_type == UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self):
            for base_index, base in enumerate(self.my_bases):
                job = (self.DEFEND_CHOKE, base_index)
                if self.count_combat_job(job, unit_type) < 2:
                    return job
        if unit_type == UnitType(UNIT_TYPEID.TERRAN_MARAUDER, self):
            for base_index, base in enumerate(self.my_bases):
                job = (self.DEFEND_CHOKE, base_index)
                if self.count_combat_job(job, unit_type) < 2:
                    return job

        return (self.STANDBY, 0)

    def count_combat_job(self, job, unit_type = None):
        if not unit_type:
            job_list = [unit for unit in self.combat_dict]
        else:
            job_list = [unit for unit in self.combat_dict if unit.unit_type == unit_type]
        if not isinstance(job, tuple):
            return len([unit for unit in job_list if self.combat_dict[unit][0] == job])
        return len([unit for unit in job_list if self.combat_dict[unit] == job])

    def execute_combat_jobs(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for unit in self.combat_dict:
            job = self.combat_dict[unit]
            if job[0] == self.DEFEND_CHOKE and unit.is_idle:
                if unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self):
                    assigned_choke = self.siege_chokes[job[1]]
                else:
                    assigned_choke = self.closest_chokes[job[1]]
                if self.count_combat_job(self.combat_dict[unit], UnitType(UNIT_TYPEID.TERRAN_MARINE, self)) >= 4:
                    if squared_distance(unit.position, assigned_choke) > 7:
                        unit.attack_move(assigned_choke)
                    elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_SIEGETANK,self):
                        unit.morph(UnitType(UNIT_TYPEID.TERRAN_SIEGETANKSIEGED,self))
            elif job[0] == self.DEFEND_BUNKER and unit.is_idle:
                assigned_bunker = self.my_bunkers.get(job[1])
                if not assigned_bunker == None and assigned_bunker.is_completed:
                    unit.right_click(assigned_bunker)
            elif job[0] == self.STANDBY and squared_distance(unit.position, self.standby_rally_point) > 7\
                    and unit.is_idle:
                unit.attack_move(self.standby_rally_point)
            elif job[0] == self.ATTACKING and unit.is_idle:
                if squared_distance(unit.position, self.attack_points[0]) < 20:
                    self.attack_points.pop(0)
                if len(self.attack_points) < 1:
                    self.init_attack_points()
                attack_point = self.attack_points[0]
                unit.attack_move(attack_point)

    def init_attack_points(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
        self.attack_points = [Point2D(base.depot_position.x, base.depot_position.y) for base in self.enemy_bases]
        start_pos = Point2D(self.get_starting_base().depot_position.x, self.get_starting_base().depot_position.y)
        enemy_start_pos = self.base_location_manager.get_player_starting_base_location(PLAYER_ENEMY).position
        self.attack_points = sorted(self.attack_points, key=lambda attack_point: squared_distance(attack_point, start_pos))
        self.attack_points.append(Point2D(enemy_start_pos.x, enemy_start_pos.y))

    def set_choke_points(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
        choke_south = Point2D(117, 54)
        choke_north = Point2D(34, 112)
        starting_pos = self.get_starting_base().position
        if squared_distance(choke_south, starting_pos) < squared_distance(choke_north, starting_pos):
            self.closest_chokes = [choke_south, Point2D(109, 75), Point2D(80, 54), Point2D(88, 79), Point2D(63, 60)]
            self.supply_depot_positions = [Point2DI(108, 19), Point2DI(106, 21), Point2DI(104, 23), Point2DI(104, 27),
                                           Point2DI(106, 25), Point2DI(108, 23), Point2DI(110, 21), Point2DI(112, 19),
                                           Point2DI(106, 29), Point2DI(108, 27), Point2DI(110, 25), Point2DI(112, 23),
                                           Point2DI(114, 21), Point2DI(116, 19), Point2DI(104, 31), Point2DI(106, 33),
                                           Point2DI(108, 31), Point2DI(110, 29), Point2DI(112, 27), Point2DI(114, 25)]
            self.barracks_positions = [Point2DI(111, 36), Point2DI(108, 33), Point2DI(115, 33), Point2DI(111, 30)]
            self.siege_chokes = [Point2D(113, 47), Point2D(112, 73), Point2D(84, 53), Point2D(88, 75), Point2D(69, 58)]
            self.standby_rally_point = Point2D(115, 43)
        else:
            self.closest_chokes = [choke_north, Point2D(43, 92), Point2D(72, 113), Point2D(66, 88), Point2D(91, 106)]
            self.supply_depot_positions = [Point2DI(43, 149), Point2DI(45, 147), Point2DI(47, 145), Point2DI(39, 149),
                                           Point2DI(41, 147), Point2DI(43, 145), Point2DI(45, 143), Point2DI(47, 141),
                                           Point2DI(37, 147), Point2DI(39, 145), Point2DI(41, 143), Point2DI(43, 141),
                                           Point2DI(45, 139), Point2DI(47, 137), Point2DI(34, 147), Point2DI(36, 145),
                                           Point2DI(37, 143), Point2DI(40, 141), Point2DI(42, 139), Point2DI(44, 137)]
            self.barracks_positions = [Point2DI(42, 134), Point2DI(39, 131), Point2DI(38, 137), Point2DI(35, 134)]
            self.siege_chokes = [Point2D(39, 120), Point2D(41, 96), Point2D(66, 117), Point2D(64, 91), Point2D(88, 110)]
            self.standby_rally_point = Point2D(35, 125)
            self.scouting_points.reverse()

            # Barracks positions North = [Point2DI(42.50, 134.50), Point2DI(39.50, 131.50),
    # Point2DI(38.50, 137.50), Point2DI(35.50, 134.50)]

    # Barracks position South = [Point2DI(111.50, 36.50), Point2DI(108.50, 33.50),
    # Point2DI(115.50, 33.50), Point2DI(111.50, 30.50)]

    def get_worker_dict(self):
        old_workers = list(self.worker_dict.keys())
        refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        for worker in old_workers:
            job = self.worker_dict[worker]
            worker_not_needed = (job[0] == self.GATHERING_MINERALS and
                                 self.count_worker_job(job) > 2 * len(self.my_minerals[job[1]]) or
                                 (job[0] == self.COLLECTING_GAS and self.count_worker_job(job) > 3))
            if job[0] == self.CONSTRUCTING and not worker.is_constructing(job[1]):
                worker_not_needed = True
            if not worker.is_alive or worker_not_needed:
                self.worker_dict.pop(worker)
            if worker_not_needed:
                worker.stop()
        my_workers = sorted(self.get_my_workers(), key=lambda worker_id: worker_id.id)
        base_locations = self.my_bases
        needed_gas_collectors = {}
        for refinery_index in self.my_refineries:
            job = (self.COLLECTING_GAS, refinery_index)
            needed_gas_collectors[refinery_index] = (3 - self.count_worker_job(job))
        needed_miners = []
        for base_number, base in enumerate(base_locations):
            minerals = self.my_minerals[base_number]
            mineral_workers = self.count_worker_job((self.GATHERING_MINERALS, base_number))
            needed_miners.append(len(minerals) * 2 - mineral_workers)
        for worker in my_workers:
            if worker not in self.worker_dict:
                for base_number, base in enumerate(base_locations):
                    if needed_miners[base_number] > 0:
                        self.worker_dict[worker] = (self.GATHERING_MINERALS, base_number)
                        needed_miners[base_number] -= 1
                        break
                    elif self.count_worker_job((self.SCOUT, 0)) < 1:
                        self.worker_dict[worker] = (self.SCOUT, 0)
                        break
                    elif needed_gas_collectors.get(base_number * 2) is not None and needed_gas_collectors[base_number * 2] > 0 :
                        self.worker_dict[worker] = (self.COLLECTING_GAS, base_number*2)
                        needed_gas_collectors[base_number * 2] -= 1
                        break
                    elif needed_gas_collectors.get(base_number * 2 + 1) is not None and needed_gas_collectors[base_number*2 +1] > 0:
                        self.worker_dict[worker] = (self.COLLECTING_GAS, base_number * 2 + 1)
                        needed_gas_collectors[base_number * 2 + 1] -= 1
                        break


    GATHERING_MINERALS = "Miner"
    COLLECTING_GAS = "Collecting gas"
    CONSTRUCTING = "Constructing"
    SCOUT = "Scouting"
    def count_worker_job(self,job):
        if isinstance(job, tuple):
            return len([worker for worker in self.worker_dict if self.worker_dict[worker] == job])
        else:
            return len([worker for worker in self.worker_dict if self.worker_dict[worker][0] == job])

    def execute_worker_jobs(self):
        refineries = self.my_refineries
        worker_dict = self.worker_dict
        for worker in list(worker_dict.keys()):
            if worker.is_idle:
                job = worker_dict[worker][0]
                job_index = worker_dict[worker][1]
                if job == self.GATHERING_MINERALS:
                    worker.right_click(random.choice(self.my_minerals[job_index]))
                elif job == self.COLLECTING_GAS and self.my_refineries.get(job_index) is not None:
                    worker.right_click(refineries[job_index])
                elif job == self.SCOUT:
                    worker.move(self.scouting_points[self.scout_counter])
                    self.scout_counter += 1
                    if self.scout_counter >= 16:
                        self.scout_counter = 0
                else:
                    self.worker_dict.pop(worker)

    def build_factory(self):
        base_locations = self.my_bases
        workers = list(self.worker_dict.keys())
        factory_type = UnitType(UNIT_TYPEID.TERRAN_FACTORY, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, factory_type))
        if amount_constructing == 0 and self.count_factories < self.count_bases and self.can_afford(factory_type)\
                and self.count_barracks >= self.count_bases and self.count_factories < 2:
            for base in base_locations:
                build_location = self.building_placer.get_build_location_near(base.depot_position, factory_type)
                if not (build_location.x == 0 and build_location.y == 0):
                    worker = random.choice(workers)
                    worker.build(factory_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, factory_type)
                    break

    def build_factory_tech_lab(self):
        factory_type = UnitType(UNIT_TYPEID.TERRAN_FACTORY, self)
        factory_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, self)
        if self.count_factories >= 1:
            for unit in self.my_units:
                if unit.unit_type == factory_type and unit.is_completed and self.can_afford(factory_tech_lab_type):
                    self.build_upgrade(unit, factory_tech_lab_type)

    def build_engineering_bay(self):
        engineering_bay_type = UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, engineering_bay_type))
        if amount_constructing == 0 and self.can_afford(engineering_bay_type) and self.count_engineering_bays < 1 \
                and self.count_barracks >= 2:
            base_locations = self.my_bases
            for base in base_locations:
                build_location = self.building_placer.get_build_location_near(base.depot_position, engineering_bay_type)
                if not (build_location.x == 0 and build_location.y == 0):
                    worker = random.choice(list(self.worker_dict.keys()))
                    worker.build(engineering_bay_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, engineering_bay_type)
                    break

    def build_starport(self):
        starport_type = UnitType(UNIT_TYPEID.TERRAN_STARPORT, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, starport_type))
        if self.count_factories > 1 and self.can_afford(starport_type) and amount_constructing == 0 \
                and self.count_starports < 1:
            base_locations = self.my_bases
            for base in base_locations:
                build_location = self.building_placer.get_build_location_near(base.depot_position, starport_type)
                if not (build_location.x == 0 and build_location.y == 0):
                    worker = random.choice(list(self.worker_dict.keys()))
                    worker.build(starport_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, starport_type)
                    break

    def build_starport_tech_lab(self):
        starport_type = UnitType(UNIT_TYPEID.TERRAN_STARPORT, self)
        starport_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_STARPORTTECHLAB, self)
        if self.count_starports >= 1:
            for unit in self.my_units:
                if unit.unit_type == starport_type and unit.is_completed and self.can_afford(starport_tech_lab_type):
                    self.build_upgrade(unit, starport_tech_lab_type)

    def build_upgrade(self, building, upgrade):  # Unit, UnitType
        if building.is_completed and self.can_afford(upgrade):
            building.train(upgrade)


    def build_bunkers(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
        chokepoints = self.closest_chokes
        base_locations = self.my_bases
        workers = list(self.worker_dict.keys())
        bunker_type = UnitType(UNIT_TYPEID.TERRAN_BUNKER, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, bunker_type))
        if self.count_bunkers < self.count_bases and self.can_afford(bunker_type) \
                and self.count_barracks >= self.count_bases and self.count_bunkers <= len(chokepoints) \
                and amount_constructing == 0:
            bunkers = [unit for unit in self.my_units if unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BUNKER, self)]
            for index in range(len(base_locations)):
                current_bunker = None
                for bunker in bunkers:
                    if squared_distance(bunker.position, chokepoints[index]) < 30:
                        current_bunker = bunker
                if not current_bunker:
                    current_choke = Point2DI(int(chokepoints[index].x), int(chokepoints[index].y))
                    #build_location = self.building_placer.get_build_location_near(current_choke, bunker_type)
                    if not (current_choke.x == 0 and current_choke.y == 0) and self.can_afford(bunker_type):
                        worker = random.choice(workers)
                        worker.build(bunker_type, current_choke)
                        self.worker_dict[worker] = (self.CONSTRUCTING, bunker_type)
                        break

    def build_barracks_old(self):
        workers = self.get_my_workers()
        barracks_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        base_location = self.my_bases
        for base in base_location:
            amount_constructing = self.count_worker_job((self.CONSTRUCTING, barracks_type))
            if amount_constructing == 0 and self.can_afford(barracks_type) and self.max_supply >= 23 \
                    and self.count_barracks < self.count_bases + 1:
                build_location = self.building_placer.get_build_location_near(base.depot_position, barracks_type)
                if not (build_location.x == 0 and build_location.y == 0):
                    worker = random.choice(workers)
                    worker.build(barracks_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, barracks_type)

    def build_barracks(self):
        workers = self.get_my_workers()
        barracks_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, barracks_type))
        if len(self.barracks_positions) == 0:
            self.set_choke_points()
        if amount_constructing == 0 and self.can_afford(barracks_type) and self.max_supply >= 23 \
                and self.count_barracks < self.count_bases + 1:
            for build_position in self.barracks_positions:
                worker = random.choice(workers)
                worker.build(barracks_type, build_position)
                self.worker_dict[worker] = (self.CONSTRUCTING, barracks_type)
                self.barracks_positions.remove(build_position)
                break

    def build_barracks_tech_lab(self):
        barracks_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        barracks_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKSTECHLAB, self)
        if self.count_factories >= 1:
            for unit in self.my_units:
                if unit.unit_type == barracks_type and unit.is_completed and self.can_afford(barracks_tech_lab_type):
                    self.build_upgrade(unit, barracks_tech_lab_type)

    def build_depots(self):
        """Constructs an additional supply depot if current supply is reaching supply maximum """
        workers = self.get_my_workers()
        supply_depot_type = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, supply_depot_type))
        if len(self.supply_depot_positions) == 0:
            self.set_choke_points()
        if (self.current_supply >= self.max_supply - 3 or self.need_more_supply) and self.max_supply < 200 \
                and amount_constructing <= self.count_bases -1 and self.can_afford(supply_depot_type):
            self.need_more_supply = False
            for build_position in self.supply_depot_positions:
                if build_position in self.supply_depot_positions:
                    worker = random.choice(workers)
                    worker.build(supply_depot_type, build_position)
                    self.worker_dict[worker] = (self.CONSTRUCTING, supply_depot_type)
                    self.supply_depot_positions.remove(build_position)
                    break

    def build_refineries(self):
        my_workers = self.get_my_workers()
        base_locations = self.my_bases
        refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, refinery_type))
        refinery_condition2 = (self.count_refineries == 0 or self.count_worker_job((self.COLLECTING_GAS, self.count_refineries -1)) >= 3)
        for base in base_locations:
            geyser_location = self.get_geysers(base)
            for index, build_location in enumerate(geyser_location):
                if amount_constructing == 0 and self.can_afford(refinery_type) \
                        and self.get_refinery(build_location) is None and self.max_supply >= 23 and refinery_condition2:
                    worker = random.choice(my_workers)
                    worker.build_target(refinery_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, refinery_type)
                    break
    """
    CONCUSSIVE_SHELLS_RESEARCHED = False
    COMBAT_SHIELDS_RESEARCHED = False

    def research_combat_shields(self):
        # .research och .train kan inte ha AbilityID som argument, hitta något annat sätt att kalla dem
        combat_shields_type = AbilityID(ABILITY_ID.RESEARCH_COMBATSHIELD)
        barracks_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKSTECHLAB, self)
        if not self.COMBAT_SHIELDS_RESEARCHED:
            self.research_upgrade(barracks_tech_lab_type, combat_shields_type)

    def research_concussive_shells(self):
        # .research och .train kan inte ha AbilityID som argument, hitta något annat sätt att kalla dem
        concussive_shells_type = AbilityID(ABILITY_ID.RESEARCH_CONCUSSIVESHELLS)
        barracks_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKSTECHLAB, self)
        if not self.CONCUSSIVE_SHELLS_RESEARCHED:
            self.research_upgrade(barracks_tech_lab_type, concussive_shells_type)
    
    ARMOUR_UPGRADE = 0
    DAMAGE_UPGRADE = 0

    def research_damage_upgrade(self):
        # Behöver kolla om botten har råd att researcha, can_afford fungerar ej för UpgradeID
        print(self.DAMAGE_UPGRADE)
        damage_upgrade_type1 = UpgradeID(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1)
        damage_upgrade_type2 = UpgradeID(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2)
        damage_upgrade_type3 = UpgradeID(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL3)
        engineering_bay_type = UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self)
        for unit in self.my_units:
            if unit.unit_type == engineering_bay_type:
                if self.minerals == 100 and self.gas == 100:
                    self.research_upgrade(engineering_bay_type, damage_upgrade_type1)
                    self.DAMAGE_UPGRADE += 1
                    break

    def research_armour_upgrade(self):
        # Behöver kolla om botten har råd att researcha, can_afford fungerar ej för UpgradeID
        print(self.ARMOUR_UPGRADE)
        armour_upgrade_type1 = UpgradeID(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL1)
        armour_upgrade_type2 = UpgradeID(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL2)
        armour_upgrade_type3 = UpgradeID(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL3)
        engineering_bay_type = UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self)
        for unit in self.my_units:
            if unit.unit_type == engineering_bay_type and unit.is_completed:
                if self.minerals == 100 and self.gas == 100:
                    self.research_upgrade(engineering_bay_type, armour_upgrade_type1)
                    self.ARMOUR_UPGRADE += 1
                    break
    """
    def research_upgrade(self, building, upgrade_type):
        my_units = self.my_units
        for unit in my_units:
            if unit.unit_type == building and unit.is_completed and unit.is_idle \
                    and isinstance(upgrade_type, UpgradeID):
                unit.research(upgrade_type)

    def build_expansion(self):
        command_centre_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        worker_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        number_of_bases = self.count_bases
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, command_centre_type))
        bases_with_minerals = []
        for index, base in enumerate(self.my_bases):
            if len(self.my_minerals[index]) >= 4:
                bases_with_minerals.append(base)
        expansion_condition = (amount_constructing == 0 and
                               self.sought_unit_counts[worker_type] <= self.count_workers +5 and
                               self.count_barracks >= 1 and
                               self.can_afford(command_centre_type) and
                               len(bases_with_minerals) < 3 and
                               self.count_refineries >= 2 * self.count_bases)
        if expansion_condition:
            build_location = self.base_location_manager.get_next_expansion(PLAYER_SELF)
            worker = random.choice(self.get_my_workers())
            worker.build(command_centre_type, build_location.depot_position)
            self.worker_dict[worker] = (self.CONSTRUCTING, command_centre_type)


    def add_counted_unit(self, unit):
        if unit.unit_type not in self.unit_counter:
            self.unit_counter[unit.unit_type] = [unit]
        else:
            self.unit_counter[unit.unit_type].append(unit)

    def count_things(self):
        self.count_bases = len(self.my_bases)
        self.count_workers = 0
        self.count_barracks = 0
        self.count_combat_units = 0
        self.count_depots = 0
        self.count_factories = 0
        self.count_bunkers = 0
        self.count_refineries = 0
        self.count_engineering_bays = 0
        self.count_starports = 0
        for unit in self.my_units:
            if unit.unit_type.is_combat_unit:
                self.count_combat_units += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_SCV, self):
                self.count_workers += 1
            elif unit.unit_type.is_supply_provider:
                self.count_depots += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self) and unit.is_completed:
                self.count_barracks += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_FACTORY, self) and unit.is_completed:
                self.count_factories += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self) and unit.is_completed:
                self.count_engineering_bays += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BUNKER, self):
                self.count_bunkers += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_REFINERY, self):
                self.count_refineries += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_STARPORT, self) and unit.is_completed:
                self.count_starports += 1

    def count_units(self):
        units_to_count = [unit for unit in self.my_units if unit.unit_type in self.sought_unit_counts]
        for unit in units_to_count:
            if unit not in self.unit_counter[unit.unit_type]:
                self.unit_counter[unit.unit_type].append(unit)
                self.add_training(unit.unit_type, -1)
        for unit_type in self.unit_counter:
            for unit in self.unit_counter[unit_type]:
                if not unit.is_alive:
                    self.unit_counter[unit_type].remove(unit)
        for unit_type in self.amount_training:
            amount_training_producers = len([producer for producer in self.get_my_producers(unit_type)
                                             if producer.is_training])
            if self.amount_training[unit_type] > amount_training_producers:
                self.amount_training[unit_type] = amount_training_producers
            if self.amount_training[unit_type] < 0:
                self.amount_training[unit_type] = 0

    def train_requests(self):
        for unit_type in self.sought_unit_counts:
            amount_wanted = self.sought_unit_counts[unit_type] - self.amount_living(unit_type) - \
                            self.amount_training[unit_type]
            if amount_wanted > 0:
                amount_trained = self.train_unit(unit_type, amount_wanted)
                self.add_training(unit_type, amount_trained)

    def amount_living(self, unit_type):
        return len(self.unit_counter[unit_type])

    def add_training(self, unit_type: UnitType, amount=1):
        self.amount_training[unit_type] = self.amount_training.get(unit_type, 0) + amount

    def request_marines(self):
        if self.keep_attacking:
            self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARINE, self), 299)
        else:
            self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARINE, self), 8*len(self.my_bases) + 12)

    def request_marauders(self):
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARAUDER, self), 2*len(self.my_bases) + 6)

    def request_tanks(self):
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self), 2*len(self.my_bases))

    def request_medivacs(self):
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MEDIVAC, self), 2*len(self.my_bases))

    def request_workers(self):
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        amount_wanted = 4
        amount_wanted += 3 * len(self.my_refineries)
        for index, base_location in enumerate(self.my_bases):
            amount_wanted += 2 * len(self.my_minerals[index])
        self.request_unit_amount(scv_type, amount_wanted)

    def request_unit_amount(self, unit_type, amount_sought):
        self.sought_unit_counts[unit_type] = amount_sought
        if unit_type not in self.amount_training:
            self.amount_training[unit_type] = 0
        if unit_type not in self.unit_counter:
            self.unit_counter[unit_type] = []

    def train_unit(self, unit_type: UnitType, amount_requested):
        """
       :param unit_type: type of unit to be trained
       :param amount_requested: amount of units requested to train
       :return: amount of units queued up
        """
        producers = self.get_my_producers(unit_type)
        amount_trained = 0
        if not self.supply_is_sufficient(unit_type):
            self.need_more_supply = True
            return amount_trained
        for producer in producers:
            if not producer.is_training and producer.is_completed:
                if self.can_afford(unit_type) and amount_requested-amount_trained > 0:
                    producer.train(unit_type)
                    amount_trained += 1

        return amount_trained

    def can_afford(self, unit_type: UnitType):
        """ Returns True if there are an sufficient amount of minerals,
        gas and supply to build the given unit_type, False otherwise """
        return self.minerals >= unit_type.mineral_price\
            and self.gas >= unit_type.gas_price\
            and self.supply_is_sufficient(unit_type)

    def supply_is_sufficient(self, unit_type: UnitType):
        return (self.max_supply - self.current_supply) >= unit_type.supply_required

    def get_my_producers(self, unit_type: UnitType):
        """ Returns a list of units which can build or train units of type unit_type """
        producers = []
        type_data = self.tech_tree.get_data(unit_type)
        what_builds = type_data.what_builds

        for unit in self.my_units:
            if unit.unit_type in what_builds and unit.unit_type.is_building:
                producers.append(unit)

        return producers

    def squared_distance(self, unit_1, unit_2):
        p1 = unit_1.position
        p2 = unit_2.position
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    def is_worker_collecting_gas(self, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        for refinery_index in self.my_refineries:
            refinery = self.my_refineries[refinery_index]
            if refinery.is_completed and self.squared_distance(worker, refinery) < 2 ** 2:
                return True

    def get_refinery(self, geyser: Unit) -> Optional[Unit]:
        """
        Returns: A refinery which is on top of unit `geyser` if any, None otherwise
        """

        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for unit in self.my_units:
            if unit.unit_type.is_refinery and squared_distance(unit.position, geyser.position) < 1:
                return unit

        return None

    def get_mineral_fields(self, base_location: BaseLocation):  # -> List[Unit]: denna del krashar koden, fråga labbass
        """
        Given a base_location, this method will find and return a list of all mineral fields (Unit) for that base
        """
        mineral_fields = []
        for mineral_field in base_location.mineral_fields:
            for unit in self.get_all_units():
                if unit.unit_type.is_mineral \
                        and mineral_field.tile_position.x == unit.tile_position.x \
                        and mineral_field.tile_position.y == unit.tile_position.y:
                    mineral_fields.append(unit)
        return mineral_fields

    def get_geysers(self, base_location: BaseLocation):  # -> List[Unit]:
        geysers = []
        for geyser in base_location.geysers:
            for unit in self.get_all_units():
                if unit.unit_type.is_geyser \
                        and geyser.tile_position.x == unit.tile_position.x \
                        and geyser.tile_position.y == unit.tile_position.y:
                    geysers.append(unit)
        return geysers


def main():
    coordinator = Coordinator(r"D:\starcraft\StarCraft II\StarCraft II\Versions\Base63454\SC2_x64.exe")
    bot1 = MyAgent()
    # bot2 = MyAgent()

    participant_1 = create_participants(Race.Terran, bot1)
    # participant_2 = create_participants(Race.Terran, bot2)
    participant_2 = create_computer(Race.Random, Difficulty.Hard)

    #coordinator.set_real_time(True)
    coordinator.set_participants([participant_1, participant_2])
    coordinator.launch_starcraft()

    path = os.path.join(os.getcwd(), "maps", "InterloperTest.SC2Map")
    coordinator.start_game(path)

    while coordinator.update():
        pass


if __name__ == "__main__":
    main()
