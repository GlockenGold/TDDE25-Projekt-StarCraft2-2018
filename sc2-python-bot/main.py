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
        self.my_units = []
        self.my_bases = []
        self.my_minerals = {}  # self.my_minerals[base_id] = list of all minerals connected to that base
        self.closest_chokes = [Point2D(116, 44)]
        self.siege_chokes = []
        self.standby_rally_point = Point2D(116, 44)
        self.scouting_points = [Point2D(60, 126), Point2D(28, 109), Point2D(28, 134), Point2D(29, 80),
                                Point2D(61, 94), Point2D(85, 112), Point2D(91, 137), Point2D(124, 135),
                                Point2D(123, 86), Point2D(89, 72), Point2D(66, 55), Point2D(28, 32),
                                Point2D(60, 31), Point2D(90, 40), Point2D(124, 57), Point2D(122, 31)]
        self.scout_counter = 0
        self.enemy_bases = []

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        self.my_units = sorted(self.get_my_units(), key=lambda unit: unit.id)
        self.manage_command_centers()
        self.get_mineral_list()
        self.get_enemy_bases()
        if self.game_ticker == 0:
            self.set_choke_points()
            self.get_mineral_list()
        elif self.game_ticker % 2 == 0:
            self.count_units()
            self.execute_combat_jobs()
        self.get_worker_dict()
        self.set_combat_dict()
        self.print_debug()
        self.print_unit_overview()
        if self.game_ticker % 2 == 0:
            self.train_requests()
        if self.game_ticker % 5 == 0:
            self.build_refineries()
            self.build_depots()
            self.build_barracks()
            self.build_expansion()
            self.build_bunkers()
            self.build_factory()
            self.build_factory_tech_lab()
            self.build_barracks_tech_lab()
            self.build_engineering_bay()
            self.request_workers()
            self.request_marines()
            self.request_tanks()
            self.request_marauders()
        self.execute_worker_jobs()
        self.game_ticker+=1

    # Ramp south: (115, 46) - (115, 43) - (118, 43)
    # Ramp north: (32, 124) - (35, 125) - (36, 121)
    # Expo 1 choke north: (44, 99)
    # Bunker 1 north: (34,112)
    # Ramp Expo South (116, 54)
    # Ramp Expo North (34, 114)

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

    def print_unit_overview(self):
        #todo: printa jobs
        self.count_bases = len(self.my_bases)
        self.count_workers = len(self.worker_dict)
        self.count_barracks = 0
        self.count_combat_units = 0
        self.count_depots = 0
        self.count_factories = 0
        self.count_bunkers = 0
        """count_miners = self.count_worker_job(self.GATHERING_MINERALS)
        count_gas_collectors =
        count_builders =
        count_scouts =
        count_choke_defenders =
        count_bunker_bois =
        count_standby =
        count attackers ="""
        for unit in self.my_units:
            if unit.unit_type.is_combat_unit:
                self.count_combat_units += 1
            elif unit.unit_type.is_supply_provider:
                self.count_depots += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self):
                self.count_barracks += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_FACTORY, self):
                self.count_factories += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self):
                self.count_engineering_bays += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BUNKER, self):
                self.count_bunkers += 1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_REFINERY, self):
                self.count_refineries += 1
        overview_string = " Bases: {} \n Workers: {} \n Refineries: {} \n Combat Units {} \n " \
                          "Supply Depots: {} \n Barracks: {} \n Factories: {} \n Bunkers: {}".format(self.count_bases,
                                                                                      self.count_workers,
                                                                                      self.count_refineries,
                                                                                      self.count_combat_units,
                                                                                      self.count_depots,
                                                                                      self.count_barracks,
                                                                                      self.count_factories,
                                                                                      self.count_bunkers)
        self.map_tools.draw_text_screen(0.005, 0.005, overview_string, Color.RED)

    def get_mineral_list(self):
        for index, base in enumerate(self.my_bases):
            self.my_minerals[index] = self.get_mineral_fields(base)

    def manage_command_centers(self):
        #todo: kolla om deathchecken fungerar.
        command_centers = self.get_my_producers(UnitType(UNIT_TYPEID.TERRAN_SCV, self))
        base_locations = self.base_location_manager.get_occupied_base_locations(PLAYER_SELF)
        for command_center in command_centers:
            command_center.right_click(command_center)
            if command_center.is_completed:
                for base in base_locations:
                    if base.contains_position(command_center.position) and base not in self.my_bases:
                        self.my_bases.append(base)
            if not command_center.is_alive and command_center in self.my_bases:
                self.my_bases.remove(command_center)


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
        start_attacking = self.count_combat_job((self.STANDBY, 0), UnitType(UNIT_TYPEID.TERRAN_MARINE, self)) >= 12 and\
                        self.count_combat_job((self.STANDBY, 0), UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self)) >= 4
        for combat_unit in old_units:
            if not combat_unit.is_alive:
                self.combat_dict.pop(combat_unit)
            elif self.combat_dict[combat_unit][0] == self.STANDBY:
                if start_attacking:
                    self.combat_dict[combat_unit] = (self.ATTACKING,0)
                else:
                    self.combat_dict[combat_unit] = self.get_combat_job(combat_unit.unit_type)
        new_combat_units = [unit for unit in self.my_units \
                if unit.unit_type.is_combat_unit and unit not in self.combat_dict]
        for new_unit in new_combat_units:
            self.combat_dict[new_unit] = self.get_combat_job(new_unit.unit_type)

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
            job_list = [unit for unit in self.combat_dict if unit.unit_type == unit_type]
        else:
            job_list = [unit for unit in self.combat_dict]
        if not isinstance(job, tuple):
            return len([unit for unit in job_list if self.combat_dict[unit][0] == job])
        return len([unit for unit in job_list if self.combat_dict[unit] == job])

    def execute_combat_jobs(self):
        #todo: point2di -> point2d
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for unit in self.combat_dict:
            job = self.combat_dict[unit]
            if job[0] == self.DEFEND_CHOKE and unit.is_idle:
                if unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self):
                    assigned_choke = self.siege_chokes[job[1]]
                else:
                    assigned_choke = self.closest_chokes[job[1]]
                if self.count_combat_job(self.combat_dict[unit]) > 4:
                    if squared_distance(unit.position, assigned_choke) > 7:
                        unit.attack_move(assigned_choke)
                    elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_SIEGETANK,self):
                        unit.morph(UnitType(UNIT_TYPEID.TERRAN_SIEGETANKSIEGED,self))
            elif job[0] == self.DEFEND_BUNKER and unit.is_idle:
                my_bunkers = [unit for unit in self.my_units if \
                              unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BUNKER, self)]
                if len(my_bunkers) > job[1]:
                    assigned_bunker = my_bunkers[job[1]]
                    if assigned_bunker.is_completed:
                        unit.right_click(assigned_bunker)
            elif job[0] == self.STANDBY and squared_distance(unit.position, self.standby_rally_point) > 7\
                    and unit.is_idle:
                unit.attack_move(self.standby_rally_point)
            elif job[0] == self.ATTACKING and unit.is_idle:
                unit.attack_move(self.enemy_bases[0].depot_position)

    def set_choke_points(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
        choke_south = Point2D(117, 54)
        choke_north = Point2D(34, 112)
        starting_pos = self.get_starting_base().position
        if squared_distance(choke_south, starting_pos) < squared_distance(choke_north, starting_pos):
            self.closest_chokes = [choke_south, Point2D(109, 75), Point2D(80, 54), Point2D(56, 76)
                , Point2D(122, 101)]
            self.siege_chokes = [Point2D(113, 47), Point2D(112, 73), Point2D(84, 53), Point2D(67, 60)]
            self.standby_rally_point = Point2D(115, 43)
        else:
            self.closest_chokes = [choke_north, Point2D(43, 92), Point2D(72, 113), Point2D(89, 104)
                , Point2D(29, 66)]
            self.siege_chokes = [Point2D(39, 120), Point2D(41, 96), Point2D(66, 117), Point2D(85, 107)]
            self.standby_rally_point = Point2D(35, 125)
            self.scouting_points.reverse()

    def get_worker_dict(self):
        old_workers = list(self.worker_dict.keys())
        for worker in old_workers:
            job = self.worker_dict[worker]
            worker_needed = not (job[0] == self.GATHERING_MINERALS and
                                 self.count_worker_job(job) > 2 * len(self.my_minerals[job[1]]) or
                                 (job[0] == self.COLLECTING_GAS and self.count_worker_job(job) > 3))
            if job[0] == self.CONSTRUCTING and not worker.is_constructing(job[1]):
                worker_needed = False
            if not worker.is_alive or not worker_needed:
                self.worker_dict.pop(worker)
            if not worker_needed:
                worker.stop()
        my_workers = sorted(self.get_my_workers(), key=lambda worker_id: worker_id.id)
        base_locations = self.my_bases
        needed_gas_collectors = []
        for refinery_index, refinery in enumerate(self.get_my_refineries()):
            job = (self.COLLECTING_GAS, refinery_index)
            needed_gas_collectors.append(3 - self.count_worker_job(job))
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
                    elif base_number * 2 < len(needed_gas_collectors) and needed_gas_collectors[base_number * 2] > 0 :
                        self.worker_dict[worker] = (self.COLLECTING_GAS, base_number*2)
                        needed_gas_collectors[base_number * 2] -= 1
                        break
                    elif base_number * 2 + 1 < len(needed_gas_collectors) and needed_gas_collectors[base_number*2 +1] > 0:
                        self.worker_dict[worker] = (self.COLLECTING_GAS, base_number * 2 + 1)
                        needed_gas_collectors[base_number * 2 + 1] -= 1
                        break
                    elif self.count_worker_job((self.SCOUT,0)) < 1:
                        self.worker_dict[worker] = (self.SCOUT, 0)
                        break

    GATHERING_MINERALS = "Miner"
    COLLECTING_GAS = "Collecting gas"
    CONSTRUCTING = "Constructing"
    SCOUT = "Scouting"
    def count_worker_job(self,job):
        return len([worker for worker in self.worker_dict if self.worker_dict[worker] == job])

    def execute_worker_jobs(self):
        #TODO: fixa refinery. Fel antal workers.
        refineries = self.get_my_refineries()
        worker_dict = self.worker_dict
        for worker in list(worker_dict.keys()):
            if worker.is_idle:
                job = worker_dict[worker][0]
                job_index = worker_dict[worker][1]
                if job == self.GATHERING_MINERALS:
                    worker.right_click(random.choice(self.my_minerals[job_index]))
                elif job == self.COLLECTING_GAS and job_index <= len(self.get_my_refineries()):
                    worker.right_click(refineries[job_index])
                elif job == self.SCOUT and worker.is_idle:
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
                    print(build_location)
                    worker = random.choice(workers)
                    worker.build(factory_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, factory_type)
                    break

    def build_engineering_bay(self):
        base_locations = self.my_bases
        workers = list(self.worker_dict.keys())
        engineering_bay_type = UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, engineering_bay_type))
        if amount_constructing == 0 and self.can_afford(engineering_bay_type) and self.count_engineering_bays < 1 \
                and self.count_barracks >= 2:
            base = random.choice(base_locations)
            build_location = self.building_placer.get_build_location_near(base.depot_position, engineering_bay_type)
            worker = random.choice(workers)
            worker.build(engineering_bay_type, build_location)
            self.worker_dict[worker] = (self.CONSTRUCTING, engineering_bay_type)

    def build_factory_tech_lab(self):
        factory_type = UnitType(UNIT_TYPEID.TERRAN_FACTORY, self)
        factory_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, self)
        if self.count_factories >= 1:
            for unit in self.my_units:
                if unit.unit_type == factory_type and unit.is_completed and self.can_afford(factory_tech_lab_type):
                    self.build_upgrade(unit, factory_tech_lab_type)

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
                    build_location = self.building_placer.get_build_location_near(current_choke, bunker_type)
                    if not (build_location.x == 0 and build_location.y == 0):
                        print(build_location)
                        worker = random.choice(workers)
                        worker.build(bunker_type, build_location)
                        self.worker_dict[worker] = (self.CONSTRUCTING, bunker_type)
                        break

    def build_barracks(self):
        workers = self.get_my_workers()
        barracks_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        base_location = self.my_bases
        for base in base_location:
            amount_constructing = self.count_worker_job((self.CONSTRUCTING, barracks_type))
            if amount_constructing == 0 and self.can_afford(barracks_type) and self.max_supply >= 23 \
                    and self.count_barracks < self.count_bases + 1:
                build_location = self.building_placer.get_build_location_near(base.depot_position, barracks_type)
                if not (build_location.x == 0 and build_location.y == 0):
                    print(build_location)
                    worker = random.choice(workers)
                    worker.build(barracks_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, barracks_type)

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
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        base_location = self.my_bases
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, supply_depot))
        for base in base_location:
            if (self.current_supply >= self.max_supply - 3 or self.need_more_supply) and self.can_afford(supply_depot) and self.max_supply < 200:
                self.need_more_supply = False
                if amount_constructing == 0:
                    build_location = self.building_placer.get_build_location_near(base.depot_position, supply_depot)
                    if not (build_location.x == 0 and build_location.y == 0):
                        print(build_location)
                        worker = random.choice(workers)
                        worker.build(supply_depot, build_location)
                        self.worker_dict[worker] = (self.CONSTRUCTING, supply_depot)

    def build_refineries(self):
        my_workers = self.get_my_workers()
        base_locations = self.my_bases
        refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, refinery_type))
        for base in base_locations:
            geyser_location = self.get_geysers(base)
            for index, build_location in enumerate(geyser_location):
                if amount_constructing == 0 and self.can_afford(refinery_type) \
                        and self.get_refinery(build_location) is None and self.max_supply >= 23:
                    worker = random.choice(my_workers)
                    worker.build_target(refinery_type, build_location)
                    self.worker_dict[worker] = (self.CONSTRUCTING, refinery_type)
                    break
    """
    CONCUSSIVE_SHELLS_RESEARCHED = False
    COMBAT_SHIELDS_RESEARCHED = False

    def research_combat_shields(self):
        combat_shields_type = AbilityID(ABILITY_ID.RESEARCH_COMBATSHIELD)
        barracks_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKSTECHLAB, self)
        if not self.COMBAT_SHIELDS_RESEARCHED:
            self.research_upgrade(barracks_tech_lab_type, combat_shields_type)

    def research_concussive_shells(self):
        concussive_shells_type = AbilityID(ABILITY_ID.RESEARCH_CONCUSSIVESHELLS)
        barracks_tech_lab_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKSTECHLAB, self)
        if not self.CONCUSSIVE_SHELLS_RESEARCHED:
            self.research_upgrade(barracks_tech_lab_type, concussive_shells_type)
    
    ARMOUR_UPGRADE = 0
    DAMAGE_UPGRADE = 0

    def research_damage_upgrade(self):
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
            if unit.unit_type == building and unit.is_completed and unit.is_idle:
                unit.research(upgrade_type)

    def build_expansion(self):
        command_centre_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        number_of_bases = self.count_bases
        amount_constructing = self.count_worker_job((self.CONSTRUCTING, command_centre_type))
        expansion_condition = (amount_constructing == 0 and self.count_workers >=21*number_of_bases and self.count_barracks >= 1
                               and self.can_afford(command_centre_type) and number_of_bases < 3)
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
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARINE, self), 8*len(self.my_bases) + 12)

    def request_marauders(self):
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARAUDER, self), 4*len(self.my_bases))

    def request_tanks(self):
        #todo: bygg i fler än en factory och rätt antal.
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self), 2*len(self.my_bases) + 4)

    def request_workers(self):
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        amount_wanted = 1
        amount_wanted += 3 * len(self.get_my_refineries())
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
        for producer in producers:
            if not producer.is_training and producer.is_completed:
                if not self.supply_is_sufficient(unit_type):
                    self.need_more_supply = True
                elif self.can_afford(unit_type) and amount_requested-amount_trained > 0:
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
            if unit.unit_type in what_builds:
                producers.append(unit)

        return producers

    def get_my_refineries(self):
        """ Returns a list of all refineries (list of Unit) """
        refineries = []
        for unit in self.my_units:
            if unit.unit_type.is_refinery and unit.is_completed:
                refineries.append(unit)
        return refineries

    def squared_distance(self, unit_1, unit_2):
        p1 = unit_1.position
        p2 = unit_2.position
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    def is_worker_collecting_gas(self, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        for refinery in self.get_my_refineries():
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
    coordinator = Coordinator(r"D:\starcraft\StarCraft II\Versions\Base67188\SC2_x64.exe")
    bot1 = MyAgent()
    # bot2 = MyAgent()

    participant_1 = create_participants(Race.Terran, bot1)
    # participant_2 = create_participants(Race.Terran, bot2)
    participant_2 = create_computer(Race.Random, Difficulty.Easy)

    #coordinator.set_real_time(True)
    coordinator.set_participants([participant_1, participant_2])
    coordinator.launch_starcraft()

    path = os.path.join(os.getcwd(), "maps", "InterloperTest.SC2Map")
    coordinator.start_game(path)

    while coordinator.update():
        pass


if __name__ == "__main__":
    main()
