
class TiedDict:

    def __init__(self, existing_dict = {}):
        self.base_dict = dict(existing_dict)#The base values
        self.ties = {'all':[]}#format: key-key, value-list of TiedDicts to update for that key(not including self)

    def __getitem__(self, item):
        return self.base_dict.get(item)

    def __setitem__(self, key, value):
        self.base_dict[key] = value

    def get_regular_dict(self):
        return self.calculate_final()

    def calculate_final(self):
        actual_dict = {}

        visited_items = []
        item_queue = [item for item in self.ties]
        while len(item_queue) > 0:
            item_visiting = item_queue.pop(0)
            visited_items.append(item_visiting)

            actual_dict[item_visiting] = 0

            visited = []
            to_visit = [self]
            while len(to_visit) > 0:
                currently_at = to_visit.pop(0)#type-TiedDict
                visited.append(currently_at)

                for item in currently_at:
                    if item not in item_queue and item not in visited_items:
                        item_queue.append(item)

                for item,value in currently_at.ties.items():
                    if item not in item_queue and item not in visited_items:
                        item_queue.append(item)
                    if item == item_visiting or item == 'all':
                        for td in value:
                            if td not in visited and td not in to_visit:
                                to_visit.append(td)

                if item_visiting in currently_at:
                    actual_dict[item_visiting] += currently_at[item_visiting]
                if item_visiting != 'all' and 'all' in currently_at:
                    actual_dict[item_visiting] += currently_at['all']

        return actual_dict

    def tie(self, other_dict, key):

        if key not in self.ties:
            self.ties[key] = []

        if key not in other_dict.ties:
            other_dict.ties[key] = []

        self.ties[key].append(other_dict)
        other_dict.ties[key].append(self)


    def __contains__(self, item):
        return item in self.base_dict

    def __iter__(self):
        return self.base_dict.__iter__()

    def items(self):
        return self.base_dict.items()

    def keys(self):
        return self.base_dict.keys()

    def values(self):
        return self.base_dict.values()

class Tie:

    def __init__(self, value):
        self._number = value
        self.tied_numbers = []

    def update(self, new_number):
        for tied_number in self.tied_numbers:
            tied_number._number = new_number

    def tie_number(self, number):
        if number != self and number not in self.tied_numbers:
            self.tied_numbers.append(number)

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value
        self.update(self._number)


    def __add__(self, other):
        return self.number + other

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        self.number += other
        return self

    def __isub__(self, other):
        self.number -= other
        return self

    def __sub__(self, other):
        return self.number - other

    def __rsub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        return self.number * other

    def __rmul__(self, other):
        return self.__mul__(other)

    def __eq__(self, other):
        return self.number == other

    def __gt__(self, other):
        return self.number > other

    def __ge__(self, other):
        return self.number >= other

    def __lt__(self, other):
        return self.number < other

    def __le__(self, other):
        return self.number <= other

    def __ne__(self, other):
        return self.number != other

    def __format__(self, format_spec):
        return format(self.number, format_spec)
