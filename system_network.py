from tied_dict import TiedDict

class SystemNetwork:

    def __init__(self, system_info):
        self.grids = []
        #format: key-grid:value-[(connector part, connected_grid),...]
        self.connections = {}
        self.system_info = system_info

    def calculate_differentials(self):
        temp_diffs = {}
        temp_sums = {}
        temp_storages = {}
        temp_caps = {}

        all_items = []

        for grid in self.grids:
            grid.calculate_base_diff()
            temp_diffs[grid] = TiedDict(grid.system_diff)
            temp_sums[grid] = TiedDict(grid.sum_system)
            temp_storages[grid] = TiedDict(grid.sum_storage)
            temp_caps[grid] = TiedDict({'all':sum([storage.system_storage.max_supply for storage in grid.storages])})
            for item in list(grid.sum_system.keys()) + list(grid.sum_storage.keys()):
                if item not in all_items:
                    all_items.append(item)

        to_remove = []
        connections_to_remove = []

        connection_queue = []

        for grid,connection_list in self.connections.items():
            if grid not in self.grids or len(connection_list) == 0:
                to_remove.append(grid)
                continue

            if grid not in connection_queue:
                connection_queue.append(grid)

            for connection_part, connected_grid in connection_list:
                if connected_grid not in self.grids:
                    connections_to_remove.append((grid,(connection_part, connected_grid)))
                    continue
                if connected_grid in self.connections and connected_grid not in connection_queue:
                    connection_queue.append(connected_grid)

        for removal in to_remove:
            del self.connections[removal]

        for key,removal in connections_to_remove:
            self.connections[key].remove(removal)

        #This queue prioritizes nested connections first
        for grid in connection_queue:
            if grid not in self.connections:
                continue
            for connection_part,connected_grid in self.connections[grid]:

                for item in all_items:
                    for _grid in [grid, connected_grid]:
                        if item not in temp_diffs[_grid]:
                            temp_diffs[_grid][item] = 0
                        if item not in temp_sums[_grid]:
                            temp_sums[_grid][item] = 0
                        if item not in temp_storages[_grid]:
                            temp_storages[_grid][item] = 0

                new_diffs,new_sums,new_storages,new_caps = connection_part.network_connector.connect(all_items, temp_diffs[grid], temp_diffs[connected_grid], temp_sums[grid], temp_sums[connected_grid], temp_storages[grid], temp_storages[connected_grid], temp_caps[grid], temp_caps[connected_grid])
                temp_diffs[grid] = new_diffs[0]
                temp_diffs[connected_grid] = new_diffs[1]
                temp_sums[grid] = new_sums[0]
                temp_sums[connected_grid] = new_sums[1]
                temp_storages[grid] = new_storages[0]
                temp_storages[connected_grid] = new_storages[1]
                temp_caps[grid] = new_caps[0]
                temp_caps[connected_grid] = new_caps[1]


        for grid in self.grids:
            calc_sum = temp_sums[grid].get_regular_dict()
            calc_diff = temp_diffs[grid].get_regular_dict()
            calc_storage = temp_storages[grid].get_regular_dict()
            calc_cap = temp_caps[grid].get_regular_dict()
            grid.set_diff(calc_sum, calc_diff, calc_storage, calc_cap)

    def add_connector(self, object, part, x, y):
        input_grid = None
        output_grid = None
        in_x, in_y = get_neighbors(x, y)[part.network_connector.get_input()]
        part.network_connector.enabled = False
        if object.is_valid_coord(in_x, in_y):
            for in_part in object.tiles[in_x][in_y]:
                if in_part.get_grid(self.system_info):
                    input_grid = in_part.get_grid(self.system_info)
                    break
        out_x, out_y = get_neighbors(x, y)[part.network_connector.get_output()]
        if object.is_valid_coord(out_x, out_y):
            for out_part in object.tiles[out_x][out_y]:
                if out_part.get_grid(self.system_info):
                    output_grid = out_part.get_grid(self.system_info)
                    break
        if input_grid and output_grid:
            if input_grid == output_grid:
                return False
            if input_grid not in self.connections:
                self.connections[input_grid] = []
            for key,connection_list in self.connections.items():
                if key == output_grid:
                    for connected_part,connected_grid in connection_list:
                        if connected_grid == input_grid:
                            #if the networks are already connected the opposite direction
                            return False
            self.connections[input_grid].append((part, output_grid))

        part.network_connector.enabled = True
        self.calculate_differentials()
        return True

    def remove_connector(self, object, part, x, y):
        for grid in self.connections:
            to_remove = None
            for connecting_part,other_grid in self.connections[grid]:
                if connecting_part == part:
                    to_remove = (connecting_part,other_grid)
                    break
            if to_remove:
                self.connections[grid].remove(to_remove)
                part.network_connector.enabled = False
                break

        self.calculate_differentials()

def get_neighbors(x, y):
    return [
        (x,y-1),
        (x+1,y),
        (x,y+1),
        (x-1,y)
    ]

