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
        self.worker_dict ={}
        self.combat_dict = {}
        self.count_bases = 0
        self.count_workers = 0
        self.count_barracks = 0
        self.count_combat_units = 0
        self.count_refineries = 0
        self.count_depots = 0
        self.my_units = []
        self.my_bases = []
        self.closest_choke = Point2D(116, 44)

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        if self.game_ticker == 0:
            self.set_choke_point()
            self.deselect_command_centers()
            self.initiate_unit_counter()
            self.my_bases.append(self.get_starting_base())
        else:
            self.count_units()
            self.execute_combat_jobs()
        self.my_units = self.get_my_units()
        self.get_worker_dict()
        self.set_combat_dict()
        self.print_unit_overview()
        self.print_debug()
        self.print_unit_overview()
        self.request_workers()
        self.request_unit_amount(UnitType(UNIT_TYPEID.TERRAN_MARINE, self),8)
        if self.game_ticker % 2 == 0:
            self.train_requests()
        if self.game_ticker % 5 == 0:
            self.build_refineries()
            self.build_depots()
            self.build_barracks()
            self.expand()
        self.start_gathering()
        self.game_ticker+=1

    # Ramp south: (115, 46) - (116, 44) - (118, 43)
    # Ramp north: (32, 124) - (35, 123) - (36, 121)

    def print_debug(self):
        my_units = self.my_units
        base_location = self.get_starting_base()
        my_minerals = base_location.minerals
        my_geysers = base_location.geysers
        for index, unit in enumerate(my_units+my_geysers+my_minerals):
            if unit.unit_type.is_worker:
                job = self.worker_dict[unit][0]
                if job == self.GATHERING_MINERALS:
                    debug_string = "<{}>".format("Miner")
                    self.map_tools.draw_text(unit.position, debug_string, Color.BLUE)
                elif job == self.COLLECTING_REFINERY_1 or self.COLLECTING_REFINERY_2:
                    debug_string = "<{}>".format("Gas Collector")
                    self.map_tools.draw_text(unit.position, debug_string, Color.GREEN)

    def print_unit_overview(self):
        self.count_bases = len(self.my_bases)
        self.count_workers = len(self.worker_dict)
        self.count_barracks = 0
        self.count_combat_units = 0
        self.count_refineries = 0
        self.count_depots = 0
        for unit in self.my_units:
            if unit.unit_type.is_refinery:
                self.count_refineries += 1
            elif unit.unit_type.is_combat_unit:
                self.count_combat_units +=1
            elif unit.unit_type.is_supply_provider:
                self.count_depots +=1
            elif unit.unit_type == UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self):
                self.count_barracks +=1
        overview_string = " Bases: {} \n Workers: {} \n Refineries: {} \n Combat Units {} \n " \
                          "Supply Depots: {} \n Barracks: {}".format(self.count_bases, self.count_workers, self.count_refineries,
                                                                     self.count_combat_units, self.count_depots,
                                                                     self.count_barracks, )
        self.map_tools.draw_text_screen(0.005,0.005,overview_string, Color.RED)

    def deselect_command_centers(self):
        command_centers = self.get_my_producers(UnitType(UNIT_TYPEID.TERRAN_SCV, self))
        for command_center in command_centers:
            command_center.right_click(command_center)

    def get_starting_base(self):
        return self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)

    def get_my_workers(self):
        workers = []
        for unit in self.my_units:  # type: Unit
            if unit.unit_type.is_worker:
                workers.append(unit)

        return workers

    def set_combat_dict(self):
        new_combat_units = sorted([unit for unit in self.get_my_units() \
                if unit.unit_type.is_combat_unit and unit not in self.combat_dict], key = lambda unit_id: unit_id.id)
        for new_unit in new_combat_units:
            self.combat_dict[new_unit] = self.get_combat_job(new_unit.unit_type)

    DEFEND = 0

    def get_combat_job(self, unit_type):
        return self.DEFEND

    def execute_combat_jobs(self):
        for unit in self.combat_dict:
            job = self.combat_dict[unit]
            if job == self.DEFEND:
                unit.move(self.closest_choke)

    def set_choke_point(self):
        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
        choke_1 = Point2D(116, 44)
        choke_2 = Point2D(35, 123)
        starting_pos = self.get_starting_base().position
        if squared_distance(choke_1, starting_pos) < squared_distance(choke_2, starting_pos):
            self.closest_choke = choke_1
        else:
            self.closest_choke = choke_2

    def get_worker_dict(self):
        my_workers = sorted(self.get_my_workers(), key=lambda worker_id: worker_id.id)
        base_locations = self.my_bases
        minerals = []
        for base_number in range(len(base_locations)):
            minerals.append(base_locations[base_number].minerals)
            mineral_workers =[scv for scv in self.worker_dict if self.worker_dict[scv][0] == self.GATHERING_MINERALS and
                              self.worker_dict[scv][1] == base_number]
            mineral_condition = len(mineral_workers) < len(minerals[base_number]) * 2
            gas_workers_1 = [scv for scv in self.worker_dict if self.worker_dict[scv][0] == self.COLLECTING_REFINERY_1
                             and self.worker_dict[scv][1] == base_number]
            gas_condition_1 = len(gas_workers_1) < 3
            gas_workers_2 = [scv for scv in self.worker_dict if self.worker_dict[scv][0] == self.COLLECTING_REFINERY_2
                             and self.worker_dict[scv][1] == base_number]
            gas_condition_2 = len(gas_workers_2) < 3
            for worker in my_workers:
                if worker not in self.worker_dict:
                    if mineral_condition:
                        self.worker_dict[worker] = [self.GATHERING_MINERALS, base_number]
                    elif gas_condition_1:
                        self.worker_dict[worker] = [self.COLLECTING_REFINERY_1, base_number]
                    elif gas_condition_2:
                        self.worker_dict[worker] = [self.COLLECTING_REFINERY_2, base_number]

    GATHERING_MINERALS = 0
    COLLECTING_REFINERY_1 = 1
    COLLECTING_REFINERY_2 = 2

    def start_gathering(self):
        base_locations = self.my_bases
        refineries = sorted(self.get_my_refineries(), key=lambda refinery_id: refinery_id.id)
        worker_dict = self.worker_dict
        for worker in worker_dict:
            if worker.is_idle:
                job = worker_dict[worker][0]
                base_number = worker_dict[worker][1]
                if job == self.GATHERING_MINERALS:
                    worker.right_click(random.choice(base_locations[base_number].minerals))
                elif job == self.COLLECTING_REFINERY_1:
                    worker.right_click(refineries[base_number*2])
                elif job == self.COLLECTING_REFINERY_2:
                    worker.right_click(refineries[base_number*2 + 1])

    def build_barracks(self):
        workers = self.get_my_workers()
        constructing_workers = []
        barracks_type = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        base_location = self.get_starting_base().depot_position

        for worker in workers:
            if worker.is_constructing(barracks_type):
                constructing_workers.append(worker)
        if len(constructing_workers) == 0 and self.can_afford(barracks_type) and self.max_supply >= 23 \
                and self.count_barracks == 0:
            build_location = self.building_placer.get_build_location_near(base_location, barracks_type)
            worker = random.choice(workers)
            worker.build(barracks_type, build_location)

    def build_depots(self):
        """Constructs an additional supply depot if current supply is reaching supply maximum """
        workers = self.get_my_workers()
        constructing_workers = []
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        base_location = self.get_starting_base().depot_position

        for worker in workers:
            if worker.is_constructing(supply_depot):
                constructing_workers.append(worker)
        if (self.current_supply >= self.max_supply - 3 or self.need_more_supply) and self.can_afford(supply_depot):
            self.need_more_supply = False
            if len(constructing_workers) == 0:
                build_location = self.building_placer.get_build_location_near(base_location, supply_depot)
                worker = random.choice(workers)
                worker.build(supply_depot, build_location)

    def build_refineries(self):
        my_workers = self.get_my_workers()
        base_location = self.get_starting_base()
        geyser_location = sorted(base_location.geysers, key=lambda geyser_id: geyser_id.id)
        refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        constructing_workers = []
        for index, build_location in enumerate(geyser_location):
            for worker in my_workers:
                if worker.is_constructing(refinery_type):
                    constructing_workers.append(worker)
            if len(constructing_workers) == 0 and self.can_afford(refinery_type) \
                    and self.get_refinery(build_location) is None and self.max_supply >= 23:
                worker = random.choice(my_workers)
                worker.build_target(refinery_type, build_location)
                self.worker_dict[worker][0] = index + 1
                break

    def initiate_unit_counter(self):
        for worker in self.get_my_workers():
            self.add_counted_unit(worker)
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)

    def add_counted_unit(self, unit):
        if unit.unit_type not in self.unit_counter:
            self.unit_counter[unit.unit_type] = [unit]
        else:
            self.unit_counter[unit.unit_type].append(unit)


    def count_units(self):
        units_to_count = [unit for unit in self.get_my_units() if unit.unit_type in self.sought_unit_counts]
        for unit in units_to_count:
            if unit not in self.unit_counter[unit.unit_type]:
                self.unit_counter[unit.unit_type].append(unit)
                self.add_training(unit.unit_type,-1)
        for unit_type in self.unit_counter:
            for unit in self.unit_counter[unit_type]:
                if not unit.is_alive:
                    self.unit_counter[unit_type].remove(unit)

    def train_requests(self):
        for unit_type in self.sought_unit_counts:
            amount_wanted = self.sought_unit_counts[unit_type] - self.amount_living(unit_type) - self.amount_training[unit_type]
            if amount_wanted > 0:
                amount_trained = self.train_unit(unit_type, amount_wanted)
                self.add_training(unit_type,amount_trained)

    def amount_living(self,unit_type):
        return len(self.unit_counter[unit_type])

    def add_training(self, unit_type: UnitType, amount = 1):
        self.amount_training[unit_type] = self.amount_training.get(unit_type, 0) + amount

    def request_workers(self):
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        amount_wanted = 0
        amount_wanted += 3 * len(self.get_my_refineries())
        for base_location in self.base_location_manager.get_occupied_base_locations(PLAYER_SELF):
            amount_wanted +=  2 * len(base_location.minerals)
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
                elif self.can_afford(unit_type) and amount_requested-amount_trained>0:
                    producer.train(unit_type)
                    amount_trained+=1

        return amount_trained

    def can_afford(self, unit_type: UnitType):
        """ Returns True if there are an sufficient amount of minerals,
        gas and supply to build the given unit_type, False otherwise """
        return self.minerals >= unit_type.mineral_price\
            and self.gas >= unit_type.gas_price\
            and self.supply_is_sufficient(unit_type)

    def supply_is_sufficient(self,unit_type: UnitType):
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
            if unit.unit_type.is_refinery:
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

    def expand(self):
        command_centre_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        number_of_bases = self.count_bases
        build_location = self.base_location_manager.get_next_expansion(PLAYER_SELF)
        expansion_condition = (self.count_workers >=21*number_of_bases and self.count_barracks >= 1
                               and self.can_afford(command_centre_type))
        if expansion_condition:
            worker = random.choice(self.get_my_workers())
            worker.build(command_centre_type, build_location.depot_position)
            self.my_bases.append(build_location)


def main():
    coordinator = Coordinator(r"D:\starcraft\StarCraft II\Versions\Base67188\SC2_x64.exe")
    bot1 = MyAgent()
    # bot2 = MyAgent()

    participant_1 = create_participants(Race.Terran, bot1)
    # participant_2 = create_participants(Race.Terran, bot2)
    participant_2 = create_computer(Race.Random, Difficulty.Easy)

    coordinator.set_real_time(True)
    coordinator.set_participants([participant_1, participant_2])
    coordinator.launch_starcraft()

    path = os.path.join(os.getcwd(), "maps", "InterloperTest.SC2Map")
    coordinator.start_game(path)

    while coordinator.update():
        pass


if __name__ == "__main__":
    main()