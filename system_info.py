from math import sqrt
import tcod

class SystemInfo:

    def __init__(self, name, storage_unit, supply_unit):
        self.name = name
        self.storage_unit = storage_unit
        self.supply_unit = supply_unit

    def is_node(self, part):
        pass

    def is_connector(self, part):
        pass

    def is_storage(self, part):
        pass

    def apply_system(self, part, system_grid):
        pass

    def get_connector_limit(self, part):
        pass

    def get_node_generation(self, part):
        pass

    def get_node_need(self, part):
        pass

    def get_colors(self):
        pass

    #This is over one hour (on game time unit)
    def convert_supply_to_storage(self, supply, supply_item):
        return supply

    def convert_storage_to_supply(self, storage, supply_item):
        return storage

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, SystemInfo) and other.name == self.name

class PowerSystem(SystemInfo):

    def __init__(self):
        SystemInfo.__init__(self, 'Power', 'MWh', 'MW')

    def is_node(self, part):
        return part.machine

    def is_connector(self, part):
        return part.wire

    def is_storage(self, part):
        return part.system_storage and part.system_storage.system_info == self

    def apply_system(self, part, system_grid):
        part.power_grid = system_grid

    def get_connector_limit(self, part):
        return part.wire.capacity

    def get_node_generation(self, part):
        return part.machine.supply_output if part.machine.enabled else [('',0)]

    def get_node_need(self, part):
        return part.machine.supply_input if part.machine.enabled else [('',0)]

    def convert_supply_to_storage(self, supply, supply_item):
        return supply

    def get_colors(self):
        return [tcod.red, tcod.orange, tcod.yellow, tcod.darkest_yellow]

class LiquidSystem(SystemInfo):

    def __init__(self):
        SystemInfo.__init__(self, 'Liquid', 'L', 'L/h')

    def is_node(self, part):
        return part.liquid_machine

    def is_connector(self, part):
        return part.liquid_pipe

    def is_storage(self, part):
        return part.system_storage and part.system_storage.system_info == self

    def apply_system(self, part, system_grid):
        part.liquid_grid = system_grid

    def get_connector_limit(self, part):
        return part.liquid_pipe.capacity

    def get_node_generation(self, part):
        return part.liquid_machine.supply_output if part.liquid_machine.enabled else [('',0)]

    def get_node_need(self, part):
        return part.liquid_machine.supply_input if part.liquid_machine.enabled else [('',0)]

    def convert_supply_to_storage(self, supply, supply_item):
        return supply

    def get_colors(self):
        return [tcod.dark_magenta, tcod.dark_blue, tcod.light_blue, tcod.lightest_blue]

class GasSystem(SystemInfo):

    def __init__(self):
        SystemInfo.__init__(self, 'Gas', 'L', 'L/h')

    def is_node(self, part):
        return part.gas_machine

    def is_connector(self, part):
        return part.gas_pipe

    def is_storage(self, part):
        return part.system_storage and part.system_storage.system_info == self

    def apply_system(self, part, system_grid):
        part.gas_grid = system_grid

    def get_connector_limit(self, part):
        return part.gas_pipe.capacity

    def get_node_generation(self, part):
        return part.gas_machine.supply_output if part.gas_machine.enabled else [('',0)]

    def get_node_need(self, part):
        return part.gas_machine.supply_input if part.gas_machine.enabled else [('',0)]

    def convert_supply_to_storage(self, supply, supply_item):
        #g/h to L

        #density in g/L
        density = 1

        return supply/density

    def convert_storage_to_supply(self, storage, supply_item):
        #L to g/h

        density = 1

        return storage * density

    def get_colors(self):
        return [tcod.darker_azure, tcod.dark_green, tcod.green, tcod.lightest_green]

class ItemSystem(SystemInfo):

    def __init__(self):
        SystemInfo.__init__(self, 'Item', 'kg', 'kg/h')

    def is_node(self, part):
        return part.item_machine

    def is_connector(self, part):
        return part.item_pipe

    def is_storage(self, part):
        return part.system_storage and part.system_storage.system_info == self

    def apply_system(self, part, system_grid):
        part.item_grid = system_grid

    def get_connector_limit(self, part):
        return part.item_pipe.capacity

    def get_node_generation(self, part):
        return part.item_machine.supply_output if part.item_machine.enabled else [('',0)]

    def get_node_need(self, part):
        return part.item_machine.supply_input if part.item_machine.enabled else [('',0)]

    def get_colors(self):
        return [tcod.dark_purple, tcod.dark_purple, tcod.purple, tcod.lighter_purple]




POWER = PowerSystem()
LIQUID = LiquidSystem()
GAS = GasSystem()
ITEM = ItemSystem()