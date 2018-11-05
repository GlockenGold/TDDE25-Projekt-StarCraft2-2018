import os

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

    def print_debug(self):
        my_units = self.get_my_units()
        base_location = self.base_location_manager.get_player_starting_base_location(0)
        my_minerals = base_location.minerals
        my_geysers = base_location.geysers
        for index, unit in enumerate(my_units+my_geysers+my_minerals):
            type = unit.unit_type.name
            id = unit.id
            debug_string = "<UnitType: '{}'> id: {} i: {}".format(type, str(id), str(index))
            self.map_tools.draw_text(unit.position, debug_string, Color.WHITE)


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