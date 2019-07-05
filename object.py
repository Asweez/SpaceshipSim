from random import randint
from copy import deepcopy
from part import Part
from system_grid import SystemGrid
from system_network import SystemNetwork
from system_info import POWER,LIQUID,GAS,ITEM

class Object:

    def __init__(self, name, width, height):
        self.name = name
        self.width = width
        self.height = height
        self.tiles = [[[] for y in range(height)] for x in range(width)] #x,y access
        self.total_mass = 0
        self.gas_rooms = []
        self.power_network = SystemNetwork(POWER)
        self.liquid_network = SystemNetwork(LIQUID)
        self.gas_network = SystemNetwork(GAS)
        self.item_network = SystemNetwork(ITEM)
        self.should_update_rooms = False

    def offset(self, offset, extend=False):
        self.width += offset[0]
        for _ in range(offset[0]):
            if extend:
                self.tiles.append([[] for y in range(self.height)])
            else:
                self.tiles.insert(0, [[] for y in range(self.height)])

        self.height += offset[1]

        for x in range(self.width):
            if extend:
                self.tiles[x].extend([[] for y in range(offset[1])])
            else:
                self.tiles[x] = [[] for y in range(offset[1])] + self.tiles[x]

    def add_part(self, x, y, part, override=False):
        if self.is_valid_coord(x,y) and all([part.sorting_index != existing_part.sorting_index for existing_part in self.tiles[x][y]]):
            if not override:
                if part.sorting_index == Part.SORTING_FRAME:
                    for nx,ny in self.get_all_neighbors(x,y):
                        if self.is_valid_coord(nx,ny) and any([part.sorting_index == Part.SORTING_FRAME for part in self.tiles[nx][ny]]):
                            break
                    else:
                        return False #Frames must be put adjacent to other frames
                elif all(part.sorting_index != Part.SORTING_FRAME for part in self.tiles[x][y]):
                    return False

            part = deepcopy(part)

            if part.network_connector:
                if not self.network_for_system_info(part.network_connector.system_info).add_connector(self, part, x, y):
                    part.network_connector.enabled = False
                    return False

            if POWER.is_node(part) or POWER.is_connector(part) or POWER.is_storage(part):
                part.power_grid = SystemGrid(POWER)
                if POWER.is_connector(part):
                    part.power_grid.add_connector(part)
                if POWER.is_node(part):
                    part.power_grid.nodes.append(part)
                if POWER.is_storage(part):
                    part.power_grid.storages.append(part)

            if LIQUID.is_node(part) or LIQUID.is_connector(part) or LIQUID.is_storage(part):
                part.liquid_grid = SystemGrid(LIQUID)
                if LIQUID.is_connector(part):
                    part.liquid_grid.add_connector(part)
                if LIQUID.is_node(part):
                    part.liquid_grid.nodes.append(part)
                if LIQUID.is_storage(part):
                    part.liquid_grid.storages.append(part)

            if GAS.is_node(part) or GAS.is_connector(part) or GAS.is_storage(part):
                part.gas_grid = SystemGrid(GAS)
                if GAS.is_connector(part):
                    part.gas_grid.add_connector(part)
                if GAS.is_node(part):
                    part.gas_grid.nodes.append(part)
                if GAS.is_storage(part):
                    part.gas_grid.storages.append(part)

            if ITEM.is_node(part) or ITEM.is_connector(part) or ITEM.is_storage(part):
                part.item_grid = SystemGrid(ITEM)
                if ITEM.is_connector(part):
                    part.item_grid.add_connector(part)
                if ITEM.is_node(part):
                    part.item_grid.nodes.append(part)
                if ITEM.is_storage(part):
                    part.item_grid.storages.append(part)


            self.tiles[x][y].append(part)
            self.tiles[x][y].sort(key=lambda x: x.sorting_index)
            self.total_mass += part.mass

            neighboring_connectors = {}

            for grid_name in part.grid_names:
                if part.__dict__[grid_name]:
                    #connect all the grids surrounding this new tile
                    flag = False
                    for nx,ny in get_neighbors(x, y):
                        if self.is_valid_coord(nx,ny):
                            for neighbor_part in self.tiles[nx][ny]:
                                grid = part.__dict__[grid_name]
                                if neighbor_part.__dict__[grid_name] and neighbor_part.__dict__[grid_name] != grid:
                                    neighbor_grid = neighbor_part.__dict__[grid_name]
                                    if grid in self.network_for_grid(grid).grids:
                                        #if we merged an existing grid, remove it
                                        self.network_for_grid(grid).grids.remove(grid)
                                    neighbor_grid.merge(grid)
                                    flag = True
                                elif neighbor_part.network_connector and neighbor_part.network_connector.system_info == grid.system_info:
                                    if self.network_for_grid(grid) not in neighboring_connectors:
                                        neighboring_connectors[self.network_for_grid(grid)] = []
                                    neighboring_connectors[self.network_for_grid(grid)].append((neighbor_part,nx,ny))

                    if not flag:
                        #if we never merged with an existing grid, that means that this grid isn't on the network yet
                        self.network_for_grid(grid).grids.append(grid)

            for grid in neighboring_connectors:
                for neighboring_connector,nx,ny in neighboring_connectors[grid]:
                    self.network_for_grid(grid).remove_connector(self, neighboring_connector, nx, ny)
                    self.network_for_grid(grid).add_connector(self, neighboring_connector, nx, ny)


            if part.blocks_gas:
                self.calculate_rooms()
            if part.power_grid:
                self.power_network.calculate_differentials()
            if part.liquid_grid:
                self.liquid_network.calculate_differentials()
            if part.gas_grid:
                self.gas_network.calculate_differentials()
            if part.item_grid:
                self.item_network.calculate_differentials()
            return True
        return False

    def update_all(self):
        for x in range(self.width):
            for y in range(self.height):
                for part in self.tiles[x][y]:
                    part.update_part(self, x, y)

        if self.should_update_rooms:
            self.calculate_rooms()
            self.should_update_rooms = False

        self.power_network.calculate_differentials()
        self.liquid_network.calculate_differentials()
        self.gas_network.calculate_differentials()
        self.item_network.calculate_differentials()

    def update_system(self, grid_name, system_info):
        segments = self.segment(lambda parts: any([part.__dict__[grid_name] for part in parts]))
        grids = []
        for segment in segments:
            new_grid = SystemGrid(system_info)
            for tile_x, tile_y in segment.tiles:
                for part in self.tiles[tile_x][tile_y]:
                    if system_info.is_connector(part):
                        new_grid.add_connector(part)
                        part.__dict__[grid_name] = new_grid
                    if system_info.is_node(part):
                        new_grid.nodes.append(part)
                        part.__dict__[grid_name] = new_grid
                    if system_info.is_storage(part):
                        new_grid.storages.append(part)
                        part.__dict__[grid_name] = new_grid
            grids.append(new_grid)


        if system_info == POWER:
            self.power_network = SystemNetwork(system_info)
        elif system_info == LIQUID:
            self.liquid_network = SystemNetwork(system_info)
        elif system_info == GAS:
            self.gas_network = SystemNetwork(system_info)
        else:
            self.item_network = SystemNetwork(system_info)

        self.network_for_system_info(system_info).grids = grids

        for x in range(self.width):
            for y in range(self.height):
                for part in self.tiles[x][y]:
                    if part.network_connector and part.network_connector.system_info == system_info:
                        self.network_for_system_info(system_info).add_connector(self, part, x, y)

        self.network_for_system_info(system_info).calculate_differentials()

    def remove_part(self, x, y, part):
        if x < len(self.tiles) and y < len(self.tiles[y]) and part in self.tiles[x][y]:
            self.total_mass -= part.mass
            self.tiles[x][y].remove(part)
            self.calculate_rooms()
            for grid_name in part.grid_names:
                if part.__dict__[grid_name]:
                    if all([not part.__dict__[grid_name] for part in self.tiles[x][y]]):
                        #If this was the only grid part (of that type) on the tile
                        self.update_system(grid_name, part.__dict__[grid_name].system_info)

            if part.network_connector:
                grid = self.network_for_system_info(part.network_connector.system_info)
                grid.remove_connector(self, part, x, y)



    def remove_part_index(self, x, y, index):
        if self.is_valid_coord(x,y):
            if 0 <= index < len(self.tiles[x][y]):
                part = self.tiles[x][y][index]
                self.remove_part(x,y,part)

    #Will segment the object into 'rooms' that satisfy the lambda condition
    def segment(self, lambda_condition):
        new_rooms = []
        checked = [[not lambda_condition(self.tiles[x][y]) for y in range(self.height)] for x in range(self.width)]
        while True:#break once there are no more rooms to check
            starting_tile = self.find_unchecked_tile(checked)
            if not starting_tile:
                break
            current_room = Room([starting_tile])
            queue = []
            start_x,start_y=starting_tile
            checked[start_x][start_y] = True
            self.add_neighbors_to_queue(start_x, start_y, queue, checked)
            while len(queue) > 0:
                tile_x,tile_y = queue.pop(0)
                if not self.is_valid_coord(tile_x, tile_y):
                    current_room.exposed = True
                    continue
                if checked[tile_x][tile_y]:
                    continue
                checked[tile_x][tile_y] = True
                current_room.tiles.append((tile_x, tile_y))
                self.add_neighbors_to_queue(tile_x, tile_y, queue, checked)
            new_rooms.append(current_room)

        return new_rooms

    def calculate_rooms(self):
        new_rooms = self.segment(lambda parts: all([not part.blocks_gas for part in parts]))
        #new method, slightly slower but ensures that oxygen is never deleted

        sum_gas = 0
        sum_tiles = 0

        for old_room in self.gas_rooms:
            for x,y in old_room.tiles:
                for new_room in new_rooms:
                    if not new_room.exposed and (x,y) in new_room.tiles:
                        # for each tile in the old rooms, find the corresponding new room and add gas for that tile
                        new_room.add_contents(old_room, 1/len(old_room.tiles))#add the kilograms of each gas that was stored in that tile (the total kilograms/the amount of tiles)
                        sum_gas += sum([old_room.gas_content[item] for item in old_room.gas_content])/len(old_room.tiles)
                        sum_tiles += 1
                        break
                else:
                    split = []
                    for neighbor in self.get_all_neighbors(x,y):
                        for new_room in new_rooms:
                            if not new_room.exposed and neighbor in new_room.tiles:
                                split.append(new_room)
                    for new_room in split:
                        new_room.add_contents(old_room, 1/(len(split) * len(old_room.tiles)))
                        sum_gas += sum([old_room.gas_content[item] for item in old_room.gas_content])/(len(old_room.tiles) * len(split))


        for new_room in new_rooms:
            if new_room.exposed:
                new_room.gas_contents = {}


        self.gas_rooms = new_rooms

    #returns a list of neighboring coordinates
    def get_all_neighbors(self, x, y):
        return [
            (x-1,y),
            (x+1,y),
            (x,y-1),
            (x,y+1)
        ]


    def add_neighbors_to_queue(self,x,y,queue,checked):
        if (x-1,y) not in queue and (not self.is_valid_coord(x-1,y) or not checked[x-1][y]):
            queue.append((x-1,y))
        if (x+1,y) not in queue and (not self.is_valid_coord(x+1,y) or not checked[x+1][y]):
            queue.append((x+1,y))
        if (x,y-1) not in queue and (not self.is_valid_coord(x,y-1) or not checked[x][y-1]):
            queue.append((x,y-1))
        if (x,y+1) not in queue and (not self.is_valid_coord(x,y+1) or not checked[x][y+1]):
            queue.append((x,y+1))

    def is_valid_coord(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def find_unchecked_tile(self, checked):
        for x in range(self.width):
            for y in range(self.height):
                if not checked[x][y]:
                    return (x,y)
        return None

    def add_part_vline(self, x, y, length, part):
        if y + length > self.height:
            self.offset((0,(y + length) - self.height), extend=True)
        for _y in range(y, y + length):
            self.add_part(x,_y, part)

    def add_part_hline(self, x, y, length, part):
        if x + length > self.width:
            self.offset(((x + length) - self.width,0), extend=True)
        for _x in range(x,x+length):
            self.add_part(_x,y, part)

    def find_room(self, x, y):
        for room in self.gas_rooms:
            for coord in room.tiles:
                if (x,y) == coord:
                    return room

        return None

    def network_for_grid(self, grid):
        if grid.system_info == POWER:
            return self.power_network
        elif grid.system_info == LIQUID:
            return self.liquid_network
        elif grid.system_info == GAS:
            return self.gas_network
        return self.item_network

    def network_for_system_info(self, system_info):
        if system_info == POWER:
            return self.power_network
        elif system_info == LIQUID:
            return self.liquid_network
        elif system_info == GAS:
            return self.gas_network

        return self.item_network

def get_neighbors(x, y):
    return [
        (x,y-1),
        (x+1,y),
        (x,y+1),
        (x-1,y)
    ]

class Room:

    def __init__(self, tiles, exposed=False):
        self.tiles = tiles
        self.exposed = exposed
        self.color = (100,100,100)
        self.gas_content = {} #Total gas content - Measured in kg

    def add_contents(self, room, modifier = 1):
        for key,value in room.gas_content.items():
            if key not in self.gas_content:
                self.gas_content[key] = 0

            self.gas_content[key] += (value * modifier)

    def calc_pressure(self):
        return calc_pressure(sum([value for value in self.gas_content.values()]), len(self.tiles))


def calc_pressure(grams_gas, volume):
    #P=(8.3 * m * T)/(V * M)
    m = grams_gas
    T = 273
    M=16 #16 g/mol is the molar mass of oxygen
    V= volume #Cubic meters
    V *= 1000 #1000 L in one cubic meter

    P = 8.3 * (m * T)/(V*M) #in atm

    return  P * 101 #101 kpa per atm
