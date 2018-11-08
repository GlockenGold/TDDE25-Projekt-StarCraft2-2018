import os
import random

from typing import Optional
from library import *


class MyAgent(IDABot):
    def __init__(self):
        IDABot.__init__(self)

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        self.print_debug()
        self.start_gathering()
        self.produce_workers()
        self.build_depots()
        self.build_refineries()

    def print_debug(self):
        my_units = self.get_my_units()
        base_location = self.get_starting_base()
        my_minerals = base_location.minerals
        my_geysers = base_location.geysers
        for index, unit in enumerate(my_units+my_geysers+my_minerals):
            unit_type = unit.unit_type.name
            unit_id = unit.id
            debug_string = "<UnitType: '{}'> id: {} i: {}".format(unit_type, str(unit_id), str(index))
            self.map_tools.draw_text(unit.position, debug_string, Color.WHITE)

    def get_starting_base(self):
        return self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)

    def get_my_workers(self):
        workers = []
        for unit in self.get_my_units():  # type: Unit
            if unit.unit_type.is_worker:
                workers.append(unit)

        return workers

    def workers_working_in_base(self, base_location):
        count_workers = 0
        my_workers = self.get_my_workers()
        for worker in my_workers:
            if self.squared_distance(worker, base_location) < 6**2:
                count_workers += 1
        return count_workers

    def get_workers_in_refinery(self, refinery):
        my_workers = self.get_my_workers()
        workers_in_refinery = []
        for worker in my_workers:
            if refinery.is_completed and self.squared_distance(worker, refinery) < 2**2:
                workers_in_refinery.append(worker)
        return workers_in_refinery

    def start_gathering(self):
        base_locations = self.base_location_manager.get_occupied_base_locations(PLAYER_SELF)
        # sorted_bases = sorted(base_locations, key=lambda base_id: base_id.id)
        my_workers = self.get_my_workers()
        sorted_workers = sorted(my_workers, key=lambda worker_id: worker_id.id)
        for base_index, base in enumerate(base_locations):
            base_minerals = base.minerals
            base_refineries = [self.get_refinery(geyser) for geyser in base.geysers if self.get_refinery(geyser) is not None]
            for worker_index, worker in enumerate(sorted_workers):
                if worker.is_idle and worker_index <= 2 * len(base_minerals):
                    chosen_mineral = random.choice(base_minerals)
                    worker.right_click(chosen_mineral)
                elif worker_index > 2 * len(base_minerals):
                    for refinery in base_refineries:
                        worker.right_click(refinery)
        """base_location = self.get_starting_base()
        my_workers = self.get_my_workers()
        base_minerals = base_location.minerals
        choose_mineral = random.choice(base_minerals)
        refineries = [refinery.is_completed for refinery in self.get_my_refineries()]
        gas_collectors = [self.is_worker_collecting_gas(worker) for worker in my_workers]
        for worker in my_workers:
            if worker.is_idle:
                worker.right_click(choose_mineral)
        """

    def produce_workers(self):
        base_location = self.get_starting_base()
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        my_workers = self.get_my_workers()
        my_command_centers = self.get_my_producers(scv_type)
        too_few = len(my_workers) < 2 * len(base_location.minerals) + 2 * len(self.get_my_refineries()) # TODO: Ta bort hårdkodning, kolla hur många workers basen har, etc.
        for center in my_command_centers:
            if too_few and self.can_afford(scv_type) and not center.is_training:
                center.train(scv_type)

    def build_depots(self):
        """Constructs an additional supply depot if current supply is reaching supply maximum """
        workers = self.get_my_workers()
        constructing_workers = []
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        base_location = self.get_starting_base().depot_position
        build_location = self.building_placer.get_build_location_near(base_location, supply_depot)
        for worker in workers:
            if worker.is_constructing(supply_depot):
                constructing_workers.append(worker)
        if self.current_supply >= self.max_supply - 1 and self.can_afford(supply_depot):
            if len(constructing_workers) == 0:
                worker = random.choice(workers)
                worker.build(supply_depot, build_location)

    def build_refineries(self):
        my_workers = self.get_my_workers()
        base_location = self.get_starting_base()
        geyser_location = [base_location.geysers for geyser in base_location.geysers if self.get_refinery(geyser) is None]
        refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        constructing_workers = []
        build_location = random.choice(geyser_location)
        for worker in my_workers:
            if worker.is_constructing(refinery_type):
                constructing_workers.append(worker)
        if len(constructing_workers) == 0 and self.can_afford(refinery_type) and self.get_refinery(build_location) == None and self.max_supply >= 23:
            worker = random.choice(my_workers)
            worker.build_target(refinery_type, build_location)

    def can_afford(self, unit_type: UnitType):
        """ Returns True if there are an sufficient amount of minerals,
        gas and supply to build the given unit_type, False otherwise """
        return self.minerals >= unit_type.mineral_price\
            and self.gas >= unit_type.gas_price\
            and (self.max_supply - self.current_supply) >= unit_type.supply_required

    def get_my_producers(self, unit_type: UnitType):
        """ Returns a list of units which can build or train units of type unit_type """
        producers = []
        type_data = self.tech_tree.get_data(unit_type)
        what_builds = type_data.what_builds

        for unit in self.get_my_units():
            if unit.unit_type in what_builds:
                producers.append(unit)

        return producers

    def get_my_refineries(self):
        """ Returns a list of all refineries (list of Unit) """
        refineries = []
        for unit in self.get_my_units():
            if unit.unit_type.is_refinery:
                refineries.append(unit)
        return refineries

    def squared_distance(self, unit_1, unit_2):
        p1 = unit_1.position
        p2 = unit_2.position
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    def is_worker_collecting_gas(self, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        def squared_distance(unit_1, unit_2):
            p1 = unit_1.position
            p2 = unit_2.position
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for refinery in self.get_my_refineries():
            if refinery.is_completed and squared_distance(worker, refinery) < 2 ** 2:
                return True

    def get_refinery(self, geyser: Unit) -> Optional[Unit]:
        """
        Returns: A refinery which is on top of unit `geyser` if any, None otherwise
        """

        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for unit in self.get_my_units():
            if unit.unit_type.is_refinery and squared_distance(unit.position, geyser.position) < 1:
                return unit

        return None


def main():
    coordinator = Coordinator(r"E:\starcraft\StarCraft II\Versions\Base67188\SC2_x64.exe")
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