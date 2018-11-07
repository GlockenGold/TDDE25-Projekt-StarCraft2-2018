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

    def start_gathering(self):
        base_location = self.get_starting_base()
        my_workers = self.get_my_workers()
        base_minerals = base_location.minerals
        for worker in my_workers:
            if worker.is_idle:
                choose_mineral = random.choice(base_minerals)
                worker.right_click(choose_mineral)

    def produce_workers(self):
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        my_workers = self.get_my_workers()
        my_command_centers = self.get_my_producers(scv_type)
        too_few = len(my_workers) < 16      # TODO: Ta bort hårdkodning, kolla hur många workers basen har, etc.
        for center in my_command_centers:
            if too_few and self.can_afford(scv_type) and not center.is_training:
                center.train(scv_type)


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

    def buld_depots(self):
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