import tcod
from random import randint
from copy import copy
from system_grid import SystemGrid
import system_info
from components import BaseComponent

class Part:

    SORTING_UNDER=0
    SORTING_FRAME=1
    SORTING_WIRE=2
    SORTING_LIQUID_PIPE=3
    SORTING_GAS_PIPE=4
    SORTING_ITEM_PIPE=5
    SORTING_MISC=6
    SORTING_MAIN=7
    SORTING_ABOVE=8
    SORTING_CEILING=9
    SORTING_ARMOR=10

    components = ['wire', 'power_grid', 'machine', 'network_connector', 'triggerable', 'runnable',
                  'system_storage', 'liquid_grid', 'liquid_pipe', 'liquid_machine', 'gas_grid', 'gas_pipe', 'gas_machine', 'item_grid', 'item_pipe', 'item_machine',
                  'rocket']
    grid_names = ['power_grid', 'liquid_grid', 'gas_grid', 'item_grid']

    def __init__(self, name, char, json_id, blocks_solids=True, blocks_liquid=True, blocks_gas=False, fg=tcod.white, bg=None, sorting_index=SORTING_MISC, mass=0.05, **kwargs):
        self.name = name
        self.char = ord(char) if type(char) is str else char
        self.fg = fg
        self.bg = bg
        self.json_id = json_id
        self.sorting_index = sorting_index #indices-0-under, 1-frame, 2-misc, 3-main, 4-above, 5-ceiling, 6-armor
        self.mass = mass
        self.blocks_solid = blocks_solids
        self.blocks_liquid = blocks_liquid
        self.blocks_gas = blocks_gas
        for key,value in kwargs.items():
            self.__dict__[key] = copy(value)
            value.part = self

        for component in self.components:
            if component not in self.__dict__:
                self.__dict__[component] = None

        if self.wire or self.machine:
            self.power_grid = SystemGrid(system_info.POWER)

        if self.liquid_pipe or self.liquid_machine:
            self.liquid_grid = SystemGrid(system_info.LIQUID)

        if self.gas_pipe or self.gas_machine:
            self.gas_grid = SystemGrid(system_info.GAS)

        if self.item_pipe or self.item_machine:
            self.item_grid = SystemGrid(system_info.ITEM)

    def update_part(self, object, x, y):
        for component in self.components:
            if component in self.__dict__ and self.__dict__[component] and isinstance(self.__dict__[component], BaseComponent):
                self.__dict__[component].update(self, object, x, y)

    #use this to dynamically change the color
    def get_render(self, object, x, y):
        for key,item in self.__dict__.items():
            if isinstance(item, BaseComponent) and item.get_render(self, object, x, y):
                return item.get_render(self, object, x, y)

        return self.char,self.fg,self.bg

    def __eq__(self, other):
        return type(other) is Part and other.name == self.name and other.char == self.char and other.__dict__ == self.__dict__

    def __str__(self):
        return 'Part: ' + self.name

    def get_grid(self, sys_info):
        if sys_info == system_info.POWER:
            return self.power_grid
        elif sys_info == system_info.LIQUID:
            return self.liquid_grid
        elif sys_info == system_info.GAS:
            return self.gas_grid

        return self.item_grid

#Using a 1,2,3,4 scale, returns list of parts at that neighbor if they exist
def get_neighbor(object, x, y, neighbor):
    if neighbor == 1:
        if object.is_valid_coord(x,y-1):
            return object.tiles[x][y-1]
    if neighbor == 2:
        if object.is_valid_coord(x+1,y):
            return object.tiles[x+1][y]
    if neighbor == 3:
        if object.is_valid_coord(x,y+1):
            return object.tiles[x][y+1]
    if neighbor == 4:
        if object.is_valid_coord(x-1,y):
            return object.tiles[x-1][y]

    return None
