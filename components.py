import tcod
import system_info

class BaseComponent():

    def get_render(self, part, object, x, y):
        return None

    def update(self, part, object, x, y):
        pass

    def get_options(self, part):
        return {}

    def change_option(self, name, new_value, part, object, x, y):
        pass

    def get_desc(self):
        return ''

def get_wire_char(object, x, y, sys_info, pipe=False):
    connections = 0
    if object.is_valid_coord(x,y-1) and any([True for part in object.tiles[x][y-1] if part.get_grid(sys_info) or (part.network_connector and part.network_connector.system_info == sys_info and (part.network_connector.get_input() == 2 or part.network_connector.get_output() == 2))]):
        connections += 1
    if object.is_valid_coord(x+1,y) and any([True for part in object.tiles[x+1][y] if part.get_grid(sys_info) or (part.network_connector and part.network_connector.system_info == sys_info and (part.network_connector.get_input() == 3 or part.network_connector.get_output() == 3))]):
        connections += 2
    if object.is_valid_coord(x,y+1) and any([True for part in object.tiles[x][y+1] if part.get_grid(sys_info) or (part.network_connector and part.network_connector.system_info == sys_info and (part.network_connector.get_input() == 0 or part.network_connector.get_output() == 0))]):
        connections += 4
    if object.is_valid_coord(x-1,y) and any([True for part in object.tiles[x-1][y] if part.get_grid(sys_info) or (part.network_connector and part.network_connector.system_info == sys_info and (part.network_connector.get_input() == 1 or part.network_connector.get_output() == 1))]):
        connections += 8

    char_dict = {
        0:7,
        1:179,
        2:196,
        3:192,
        4:179,
        5:179,
        6:218,
        7:195,
        8:196,
        9:217,
        10:196,
        11:193,
        12:191,
        13:180,
        14:194,
        15:197
    }
    pipe_dict = {
        0:9,
        1:186,
        2:205,
        3:200,
        4:186,
        5:186,
        6:201,
        7:204,
        8:205,
        9:188,
        10:205,
        11:202,
        12:187,
        13:185,
        14:203,
        15:206
    }

    if pipe:
        return pipe_dict.get(connections)
    return char_dict.get(connections)

class Connector(BaseComponent):

    def __init__(self, capacity, sys_info, pipe=False):
        self.capacity = capacity
        self.sys_info = sys_info
        self.pipe = pipe

    def get_render(self, part, object, x, y):
        colors = self.sys_info.get_colors()
        color = colors[3]
        if part.get_grid(self.sys_info).get_sum_system() > part.get_grid(self.sys_info).capacity:
            color = colors[0]
        if part.get_grid(self.sys_info).full:
            color = tcod.desaturated_sea
        if part.get_grid(self.sys_info).supplied:
            if part.get_grid(self.sys_info).get_sum_system() >= part.get_grid(self.sys_info).capacity * 0.8:
                color = colors[1]
            else:
                color = colors[2]
        return get_wire_char(object, x, y, self.sys_info, pipe=self.pipe),color,part.bg

class Machine(BaseComponent):

    def __init__(self, input=[('',0)], output=[('',0)]):
        BaseComponent.__init__(self)
        self.supply_output = output
        self.supply_input = input
        self.enabled = True

    def requires_supplies(self):
        for item,value in self.supply_input:
            if item != '' and value > 0:
                return True
        return False

    def generates_supplies(self):
        for item,value in self.supply_output:
            if item != '' and value > 0:
                return True
        return False

class NetworkConnector(BaseComponent):

    def __init__(self, system_info):
        self.enabled = True
        self.system_info = system_info
        self.input_dir = 0
        self.output_dir = 2
        self.on = True

    def get_render(self, part, object, x, y):
        default_render = self.nc_render(part, object, x, y)
        return default_render[0], (tcod.red if not self.enabled else default_render[1]),default_render[2]

    def nc_render(self, part, object, x, y):
        return part.char,part.fg,part.bg

    def connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        for item in items:
            if item not in in_diff:
                in_diff[item] = 0
            if item not in in_sum:
                in_sum[item] = 0
            if item not in out_diff:
                out_diff[item] = 0
            if item not in out_sum:
                out_sum[item] = 0
            if item not in in_bc:
                in_bc[item] = 0
            if item not in out_bc:
                out_bc[item] = 0
        return self.subclass_connect(items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap)

    def subclass_connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        return (in_diff, out_diff),(in_sum, out_sum),(in_bc,out_bc),(in_cap, out_cap)

    def get_desc(self):
        string = self.nc_desc()
        if not self.enabled:
            string = 'WARNING: This part is disabled\n' + string
        return string

    def nc_desc(self):
        return ''

    def get_input(self):
        return self.input_dir

    def get_output(self):
        return self.output_dir

    def get_options(self, part):
        return {
            'Status':(['Off', 'On'],int(self.on)),
            'Input':(['N', 'E', 'S', 'W'], self.input_dir),
            'Output': (['N', 'E', 'S', 'W'], self.output_dir)
        }

    def change_option(self, name, new_value, part, object, x, y):
        flag = False
        if name == 'Input':
            if new_value != self.output_dir:
                self.input_dir = new_value
                flag = True
        elif name == 'Status':
            self.on = new_value == 1 and self.enabled
        elif name == 'Output':
            if new_value != self.input_dir:
                self.output_dir = new_value
                flag = True

        if flag:
            object.network_for_system_info(self.system_info).remove_connector(object, part, x, y)
            object.network_for_system_info(self.system_info).add_connector(object, part, x, y)

class Transformer(NetworkConnector):

    def __init__(self, input_wattage, output_wattage):
        NetworkConnector.__init__(self, system_info.POWER)
        self.input_wattage = input_wattage
        self.output_wattage = output_wattage
        self.input_dir = 0
        self.output_dir = 2

    def subclass_connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        item = 'power'
        if out_sum[item] < self.output_wattage and 0 < in_diff[item] <= self.input_wattage:
            # if there is an actual need on the output side
            need = self.output_wattage - out_sum[item]
            effective_in_diff = in_diff[item]
            if effective_in_diff < need:
                #if the input diff doesn't cover the output need, use input battery charge
                effective_in_diff = min(in_diff[item] + in_bc[item], need)

            power_transformed = min(self.output_wattage - out_sum[item], effective_in_diff)
            #This won't ever use battery charge from the output grid
            #If we drew battery charge from the input grid (aka effective diff is more than the actual diff) then we send that back in all three tuples
            # (differential because it is increasing the differential of the input grid up to the need of the output grid)
            # (sum because the charge from the battery is traveling through the input grid as well)
            # (battery charge because the charge is being pulled from the input grid)
            return (effective_in_diff - min(power_transformed, -out_diff[item]),out_diff[item] + power_transformed),(in_sum[item] + (effective_in_diff - in_diff[item]),out_sum[item] + power_transformed + (effective_in_diff - in_diff[item])),(in_bc[item] - (effective_in_diff - in_diff[item]),out_bc[item]),(in_cap, out_cap)
        else:
            return super().subclass_connect(items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap)

    def nc_desc(self):
        return 'Transforms {} W input to {} W output'.format(self.input_wattage, self.output_wattage)

class Switch(NetworkConnector):

    def __init__(self, system_info):
        NetworkConnector.__init__(self, system_info)

    def subclass_connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        if self.on:
            for item in items:
                switch_connect(item, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc)

            in_cap.tie(out_cap, 'all')

            return (in_diff, out_diff), (in_sum, out_sum), (in_bc, out_bc),(in_cap, out_cap)
        else:
            return super().subclass_connect(items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap)

    def nc_render(self, part, object, x, y):
        return part.char, (tcod.light_yellow if self.on else tcod.dark_yellow), part.bg

class Door(BaseComponent):

    def __init__(self, closed_char, open_char):
        self.closed_char = closed_char
        self.open_char = open_char

    def get_options(self, part):
        return {
            'State':(['Closed', 'Open'], int(not part.blocks_gas))
        }

    def change_option(self, name, new_value, part, object, x, y):
        self.opened = new_value == 1
        part.blocks_gas = not self.opened
        object.should_update_rooms = True

    def get_render(self, part, object, x, y):
        return (ord(self.closed_char) if part.blocks_gas else ord(self.open_char)),part.fg, part.bg

class SystemStorage(BaseComponent):

    def __init__(self, capacity, system_info, auto_discharge = -1):
        self.system_info = system_info
        self.contents = {}
        self.max_supply = capacity
        #The diff that the battery can dispense by itself every tick (-1 for unlimited)
        self.auto_discharge = auto_discharge

    def calculate_supply(self):
        sum = 0
        for item,value in self.contents.items():
            sum += value
        return sum

    def get_desc(self):
        desc_string = 'Max Discharge: {}\n'.format(self.auto_discharge)
        for key,value in self.contents.items():
            desc_string += '{0}: {1:.2f} {2}\n'.format(key, value, self.system_info.storage_unit)
        return desc_string

class Battery(SystemStorage):

    def __init__(self, capacity):
        SystemStorage.__init__(self, capacity, system_info.POWER)
        self.current_charge = 0
        self.max_charge = capacity

    def get_render(self, part, object, x, y):
        return part.char, (tcod.green if self.current_charge > 0 else tcod.dark_green),part.bg

class Runnable(BaseComponent):

    def __init__(self, run_func=None):
        if run_func:
            self.run_func = run_func
        else:
            self.run_func = default_runnable
        self.on = True
        self.functioning = False
        self.error_message = ''

    def run(self, object, part, x, y):
        if self.on:

            self.error_message = self.run_func(part, object, x, y)
            self.functioning = self.error_message == ''

            if not self.functioning and 'full' not in self.error_message:
                everything_in_storage = True

                if 'power' in self.error_message and part.machine and part.machine.requires_supplies():
                    if 'power' not in part.power_grid.sum_storage or part.power_grid.sum_storage['power'] < part.machine.supply_input[0][1]:
                        everything_in_storage = False

                if 'liquid' in self.error_message and part.liquid_machine and part.liquid_machine.requires_supplies():
                    for key,value in part.liquid_machine.supply_input:
                        if not part.liquid_grid.item_in_pipes(key, value):
                            everything_in_storage = False
                if 'gas' in self.error_message and part.gas_machine and part.gas_machine.requires_supplies():
                    for key,value in part.gas_machine.supply_input:
                        if not part.gas_grid.item_in_pipes(key, value):
                            everything_in_storage = False

                self.functioning = everything_in_storage
                if self.functioning:
                    self.error_message = ''

        else:
            self.functioning = False
            self.error_message = 'Machine turned off'

    def get_options(self, part):
        return {
            'Enabled':(['No','Yes'],int(self.on))
        }

    def change_option(self, name, new_value, part, object, x, y):
        self.change_state(part, new_value == 1)


    def change_state(self, part, new_state):
        self.on = new_state
        for component_name in part.components:
            if part.__dict__[component_name] and isinstance(part.__dict__[component_name], Machine):
                part.__dict__[component_name].enabled = self.on

    def get_render(self, part, object, x, y):
        return part.char,(tcod.red if not self.on else (tcod.orange if not self.functioning else part.fg)),part.bg

    def get_desc(self):
        return 'Operational: ' + ('Yes' if self.functioning and self.on else 'No') + '\nError Message: {}'.format(self.error_message)

class Pump(NetworkConnector):

    def __init__(self, system_info, output_supply):
        NetworkConnector.__init__(self, system_info)
        self.output_supply = output_supply

    def subclass_connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        sum_out_bc = sum([value for value in out_bc.values()])
        sum_out_cap = sum([value for value in out_cap.values()])

        if sum_out_bc < sum_out_cap and self.on:

            sum_diff = sum([value for value in in_diff.values()])
            sum_bc = sum([value for value in in_bc.values()])
            remaining_pump_capacity = self.output_supply

            if sum_diff > 0:

                proportion = min(1,remaining_pump_capacity / sum_diff)  # This pump will pull the same proportion of fluid that exists in the input diff, if any

                for item in in_diff:
                    amount_pulled = in_diff[item] * proportion
                    in_diff[item] -= amount_pulled
                    out_diff[item] += amount_pulled
                    out_sum[item] += amount_pulled
                    remaining_pump_capacity -= amount_pulled

            if sum_bc > 0:

                proportion = min(1,remaining_pump_capacity / sum_bc)  # This pump will pull the same proportion of fluid that exists in the input storage, if any

                if proportion > 0:

                    for item in in_bc:
                        amount_pulled = in_bc[item] * proportion
                        in_bc[item] -= amount_pulled
                        in_sum[item] += amount_pulled
                        out_diff[item] += amount_pulled
                        out_sum[item] += amount_pulled
                        remaining_pump_capacity -= amount_pulled


            return (in_diff,out_diff),(in_sum,out_sum),(in_bc,out_bc),(in_cap, out_cap)

        return super().subclass_connect(items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap)

    def get_options(self, part):
        options= super().get_options(part)
        options['Output Amount']=(['-',str(self.output_supply),'+'], 1)
        return options

    def change_option(self, name, new_value, part, object, x, y):
        super().change_option(name, new_value, part, object, x, y)
        if name == 'Output Amount':
            if new_value == 0 and self.output_supply > 1:
                self.output_supply -= 1
            if new_value == 2 and self.output_supply < 10:
                self.output_supply += 1

class Vent(SystemStorage):

    def __init__(self, vent_rate, max_pressure, system_info):
        SystemStorage.__init__(self, vent_rate, system_info, auto_discharge=0)
        self.max_pressure = max_pressure

    def update(self, part, object, x, y):
        if object.find_room(x, y):
            room = object.find_room(x, y)

            if room.exposed:
                self.contents = {}
                return

            density = 1.5 #g/L

            grams_stored = min(self.max_supply, self.calculate_supply()) * density

            vent_modifier = 1

            sum_room_gas = sum([value for value in room.gas_content.values()])
            current_pressure = calc_pressure(sum_room_gas, len(room.tiles))

            if current_pressure >= self.max_pressure:
                return

            all_gas = sum_room_gas + grams_stored

            if calc_pressure(all_gas, len(room.tiles)) > self.max_pressure:
                vent_modifier = (self.max_pressure-calc_pressure(sum_room_gas, len(room.tiles)))/calc_pressure(grams_stored,len(room.tiles))

            for item,value in self.contents.items():
                if item not in room.gas_content:
                    room.gas_content[item] = 0
                room.gas_content[item] += value * density * vent_modifier
            self.contents = {}

class Intake(Machine):

    def __init__(self, system_info, intake_capacity):
        Machine.__init__(self)
        self.system_info = system_info
        self.intake_capacity = intake_capacity
        self.functioning = False

    def update(self, part, object, x, y):
        if default_runnable(part, object, x, y) == '':
            self.supply_output = []
            room = object.find_room(x, y)
            if room:
                sum_room_gas = sum([value for value in room.gas_content.values()]) #in g

                density = 1.5 #g/L

                sum_room_liters = sum_room_gas / density

                if sum_room_liters > 0:

                    proportion = min(1, self.intake_capacity/sum_room_liters)

                    for item,value in room.gas_content.items():
                        self.supply_output.append((item,value * proportion / density))
                        room.gas_content[item] -= value * proportion

            self.functioning = True
        else:
            self.supply_output = []
            self.functioning = False

    def get_render(self, part, object, x, y):
        return part.char, (tcod.orange if not self.functioning else part.fg),part.bg

class Filter(NetworkConnector):

    def __init__(self, system_info):
        NetworkConnector.__init__(self, system_info)
        self.whitelist = []
        self.item_options = []

    def connect(self, items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap):
        self.item_options = items
        if self.on:

            for item in items:
                if item in self.whitelist:
                    switch_connect(item, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc)
                    in_cap.tie(out_cap, item)

            return (in_diff, out_diff), (in_sum, out_sum), (in_bc, out_bc), (in_cap, out_cap)

        return super().connect(items, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc, in_cap, out_cap)

    def get_desc(self):
        return self.system_info.name + ' Filter:\n'

    def get_options(self, part):
        options = super().get_options(part)
        for item in self.item_options:
            options[item.capitalize()] = (['No', 'Yes'], int(item in self.whitelist))
        return options

    def change_option(self, name, new_value, part, object, x, y):
        super().change_option(name, new_value, part, object, x, y)
        if name.lower() in self.item_options:
            if new_value == 1 and name.lower() not in self.whitelist:
                self.whitelist.append(name.lower())
            elif new_value == 0 and name.lower() in self.whitelist:
                self.whitelist.remove(name.lower())

class Rocket(BaseComponent):

    def __init__(self, max_thrust):
        BaseComponent.__init__(self)
        self.max_thrust = max_thrust #in kN

def default_runnable(part, object, x, y):
    if part.machine:
        if part.machine.requires_supplies() and not part.power_grid.supplied:
            return 'Not enough power'
    if part.liquid_machine:
        if part.liquid_machine.requires_supplies() and not part.liquid_grid.supplied:
            return 'Not enough liquid input'
        if part.liquid_machine.generates_supplies() and (part.liquid_grid.full or part.liquid_grid.get_sum_system() > part.liquid_grid.capacity):
            return 'Liquid output full'
    if part.gas_machine:
        if part.gas_machine.requires_supplies() and not part.gas_grid.supplied:
            return 'Not enough gas input'
        if part.gas_machine.generates_supplies() and (part.gas_grid.full or part.gas_grid.get_sum_system() > part.gas_grid.capacity):
            return 'Gas output full'
    if part.item_machine:
        if part.item_machine.requires_supplies() and not part.item_grid.supplied:
            return 'Not enough item input'
        if part.item_machine.generates_supplies() and (part.item_grid.full or part.item_grid.get_sum_system() > part.item_grid.capacity):
            return 'Item output full'

    return ''

def calc_pressure(grams_gas, volume):
    #P=(8.3 * m * T)/(V * M)
    m = grams_gas
    T = 273
    M=16 #16 g/mol is the molar mass of oxygen
    V= volume #Cubic meters
    V *= 1000 #1000 L in one cubic meter

    P = 8.3 * (m * T)/(V*M) #in atm

    return  P * 101 #101 kpa per atm

def calc_grams(pressure, volume):
    P=pressure/101 #atm
    T=273
    M=16
    V = volume
    V *= 1000

    m = (P*V*M)/(8.3*T)

    return m

def switch_connect(item, in_diff, out_diff, in_sum, out_sum, in_bc, out_bc):
    sum_diff = in_diff[item] + out_diff[item]
    sum_power = in_sum[item] + out_sum[item]
    sum_bc = in_bc[item] + out_bc[item]
    charge_pulled_total = 0
    if sum_diff < 0 and sum_bc > 0:
        new_sum_diff = min(0, sum_diff + sum_bc)
        charge_pulled_total = (new_sum_diff - sum_diff)
        sum_bc -= charge_pulled_total
        sum_diff = new_sum_diff
        sum_power += charge_pulled_total

    in_diff.tie(out_diff, item)
    in_sum.tie(out_sum, item)
    in_bc.tie(out_bc, item)
