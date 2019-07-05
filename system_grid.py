from random import randint
from system_info import SystemInfo,POWER
from components import BaseComponent,SystemStorage
from collections import namedtuple

GridStorage = namedtuple('GridStorage', ['system_storage', 'gas_grid', 'liquid_grid', 'power_grid', 'item_grid'])

class SystemGrid(BaseComponent):

    def __init__(self, system_info):
        self.nodes = []
        self.connectors = []
        self.grid_storage = GridStorage(system_storage=SystemStorage(1,system_info), gas_grid=self if system_info.name == 'Gas' else None, liquid_grid=self if system_info.name == 'Liquid' else None, power_grid=self if system_info.name == 'Power' else None, item_grid=self if system_info.name == 'Item' else None,)

        self.storages = [self.grid_storage]
        self.sum_storage = {}
        self.sum_system = {}
        self.system_diff = {}
        self.sum_cap = {}
        self.supplied = False
        self.capacity = 0
        self.index = randint(0,999)
        self.system_info:SystemInfo = system_info
        self.full = False

    def merge(self, system_grid):
        self.nodes.extend(system_grid.nodes)
        self.connectors.extend(system_grid.connectors)
        self.storages.extend(system_grid.storages)
        for node in system_grid.nodes:
            self.system_info.apply_system(node, self)
        for connector in system_grid.connectors:
            self.system_info.apply_system(connector, self)
            if self.system_info.get_connector_limit(connector) < self.capacity or self.capacity == 0:
                self.capacity = self.system_info.get_connector_limit(connector)
        for storage in system_grid.storages:
            if type(storage) is not GridStorage:
                self.system_info.apply_system(storage, self)
            else:
                self.storages.remove(storage)


    def add_connector(self, connector_part):
        self.connectors.append(connector_part)
        if self.system_info.get_connector_limit(connector_part) < self.capacity or self.capacity == 0:
            self.capacity = self.system_info.get_connector_limit(connector_part)

    def calculate_base_diff(self):

        self.sum_system = {}
        self.system_diff = {}
        self.sum_storage = {}
        self.grid_storage.system_storage.max_supply = sum([self.system_info.get_connector_limit(part) for part in self.connectors]) + len(self.nodes)

        for node in self.nodes:
            if node.runnable and (not node.runnable.on or (not node.runnable.functioning and self.system_info != POWER)):
                continue
            for item,supply in self.system_info.get_node_generation(node):
                if item != '':
                    if item not in self.sum_system:
                        self.sum_system[item] = 0
                    self.sum_system[item] += supply
            for item,supply in self.system_info.get_node_need(node):
                if item != '':
                    if item not in self.system_diff:
                        self.system_diff[item] = 0
                    self.system_diff[item] -= supply
                    self.full = False

        for part in self.storages:
            storage = part.system_storage
            if storage.calculate_supply() > 0:
                for item in storage.contents:

                    if item not in self.sum_system:
                        self.sum_system[item] = 0
                    if item not in self.system_diff:
                        self.system_diff[item] = 0
                    if item not in self.sum_storage:
                        self.sum_storage[item] = 0

                    potential_diff = self.system_info.convert_storage_to_supply(storage.contents[item], None)
                    self.sum_storage[item] += potential_diff
                    if storage.auto_discharge != -1:
                        potential_diff = min(storage.auto_discharge, potential_diff)

                    # self.system_diff[item] = min(self.system_diff[item] + potential_diff, self.capacity)
                    # self.sum_system[item] = min(self.sum_system[item] + potential_diff, self.capacity)

                    if self.sum_system[item] < -self.system_diff[item]:
                        supply_pulled = min(-self.system_diff[item] - self.sum_system[item], potential_diff)
                        self.sum_storage[item] -= self.system_info.convert_supply_to_storage(supply_pulled, None)
                        self.sum_system[item] += supply_pulled

            if storage.calculate_supply() < storage.max_supply:
                self.full = False

        for item in self.sum_system:
            if item not in self.system_diff:
                self.system_diff[item] = 0

        for item in self.system_diff:
            if item in self.sum_system:
                self.system_diff[item] += self.sum_system[item]


    def set_diff(self, sum_system, diff, storage, cap_dict):
        #format of cap dict: if the item is in the dict, the capacity for that item is the value, otherwise the capacity for that item is the value of key 'all'
        self.sum_system = sum_system
        self.system_diff = diff
        storage_change = {}
        for item,value in storage.items():
            if item not in self.sum_storage:
                self.sum_storage[item] = 0
            storage_change[item] = value - self.sum_storage[item]
        self.sum_storage = storage
        self.sum_cap = cap_dict

        all_items = []
        for item in list(sum_system.keys()) + list(diff.keys()) + list(storage.keys()):
            if item not in all_items:
                all_items.append(item)

        sum_all_diffs = sum([value for value in self.system_diff.values()])
        sum_all_storage = sum([value for value in storage.values()])
        sum_all_change = sum([value for value in storage_change.values()])

        self.full = False

        if self.get_sum_system() <= self.capacity:
            for item in all_items:

                fill_amount = 0
                fill_amount_from_diff = 0
                take_amount = 0
                if sum_all_storage > 0:
                    storage_proportion = self.sum_storage[item]/sum_all_storage
                else:
                    storage_proportion = 0

                if sum_all_diffs > 0:
                    diff_proportion = self.system_diff[item]/sum_all_diffs
                else:
                    diff_proportion = 0

                if item in cap_dict:
                    cap = cap_dict[item]

                    sum_item_storage = sum([value for storage_item,value in self.sum_storage.items() if storage_item == item])
                    sum_item_diff = sum([value for storage_item,value in self.system_diff.items() if storage_item == item])
                    sum_item_change = sum([value for storage_item,value in storage_change.items() if storage_item == item])

                    if sum_item_storage > 0:
                        storage_proportion = self.sum_storage[item]/sum_item_storage
                    else:
                        storage_proportion = 0

                    if sum_item_diff > 0:
                        diff_proportion = self.system_diff[item]/sum_item_diff
                    else:
                        diff_proportion = 0

                    if cap > 0:
                        fill_amount = min(1, sum_item_storage / cap)
                        fill_amount_from_diff = max(0, min(1, sum_item_diff / cap))
                        take_amount = min(1, -sum_item_change / cap)
                else:
                    cap = cap_dict['all']

                    if cap > 0:

                        fill_amount = min(1, sum_all_storage / cap)
                        fill_amount_from_diff = max(0, min(1, sum_all_diffs / cap))
                        take_amount = min(1, -sum_all_change / cap)


                if item not in self.system_diff:
                    self.system_diff[item] = 0
                for part in self.storages:
                    storage = part.system_storage

                    storage.contents[item] = 0

                    if item in self.sum_storage and sum_all_storage > 0:
                        storage.contents[item] += (fill_amount * storage_proportion * storage.max_supply)

                    if sum_all_diffs > 0:
                        storage.contents[item] = min(storage.contents[item] + (fill_amount_from_diff * diff_proportion * storage.max_supply), storage.max_supply)


        self.full = self.grid_storage.system_storage.calculate_supply() >= self.grid_storage.system_storage.max_supply
        self.supplied = any([item in diff and item in sum_system and diff[item] >= 0 and self.capacity >= sum_system[item] > 0 for item in self.sum_system])


    def get_sum_system(self):
        sum = 0
        for item,value in self.sum_system.items():
            sum += value

        return sum

    def is_stressed(self):
        return self.get_sum_system() >= self.capacity * 0.8

    def get_desc(self):
        # string = self.system_info.name + ':' + str(self.index)
        # string += '\nDiff: \n\n{}'.format(self.format_dict(self.system_diff, self.system_info.supply_unit))
        # string += '\n\nSum: \n\n{}'.format(self.format_dict(self.sum_system, self.system_info.supply_unit))
        #
        # stored = {}
        #
        # for key,value in self.system_diff.items():
        #     stored[key] = value
        # for key,value in self.sum_storage.items():
        #     if key not in stored:
        #         stored[key] = 0
        #     stored[key] += value
        #
        # string += '\n\nStorage Potential: \n\n{}'.format(self.format_dict(stored, self.system_info.supply_unit))
        string = 'Throughput: {0:.2f} / {1:.2f} {2}\n'.format(self.get_sum_system(), self.capacity, self.system_info.supply_unit)

        storage_list = ['{4} - {0:.2f}/{3:.2f} {1} ({2:.2f}% capacity)'.format(value, self.system_info.storage_unit, 100 * value/(self.sum_cap[item] if item in self.sum_cap else self.sum_cap['all']), (self.sum_cap[item] if item in self.sum_cap else self.sum_cap['all']), item.capitalize()) for item,value in self.sum_storage.items() if item != 'all' and (value > 0 or (item in self.sum_cap and self.sum_cap[item] > 0))]

        string += 'Storage:\n{}\n'.format(',\n'.join(storage_list))
        return string

    def format_dict(self, dict, unit):
        return ',\n'.join(['{0}:{1:.2f} {2}'.format(item, value, unit) for item,value in dict.items()])

    def __repr__(self):
        return '{} {}'.format(self.system_info.name, self.index)

    def item_in_pipes(self, item, amount):
        return item in self.grid_storage.system_storage.contents and self.grid_storage.system_storage.contents[item] >= amount
