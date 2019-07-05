import os
from os import walk
import json
from part import Part
import part
import components
import inspect
import system_info

all_components = []

def parse(dct, object_list, subdir='objects'):
    all_components = [m for m in inspect.getmembers(components, inspect.isclass) if m[1].__module__ == 'components']

    obj_dec = ObjectDecoder(all_components)
    for (dirpath, dirnames, filenames) in walk(os.getcwd() + '/' + subdir):
        for filename in sorted(filenames):
            if filename[0] == '.':
                continue
            item = load_item(open(dirpath + '/' + filename), obj_dec, filename)
            find_list(dct, subdir, dirpath).append(item)
            object_list.append(item)

def find_list(dict, sub_dir, cur_path):
    obj = dict
    tracing = False
    for string in cur_path.split('/'):
        if string == sub_dir:
            tracing = True
        elif tracing:
            if string not in obj:
                if string == cur_path.split('/')[-1]:
                    obj[string] = []
                else:
                    obj[string] = {}
            obj = obj[string]
    return obj

def load_item(json_string, object_dec, json_filename):
    s = json_string.read()
    jdict = json.loads(s, object_hook=object_dec.decode_component)
    jdict.__dict__['json_id'] = json_filename
    item = Part(**(jdict.to_dict()))
    return item

class ObjectDecoder:

    def __init__(self, item_list):
        self.item_list = item_list

    def decode_component(self, dct):
        dc = DefaultComponent()
        tuple_flag = False
        for key,value in dct.items():
            if key == '__tuple__':
                tuple_flag = True
                continue
            if key == 'sorting_index' and value in part.Part.__dict__:
                value = part.Part.__dict__[value]
            if value == 'POWER':
                value = system_info.POWER
            if value == 'LIQUID':
                value = system_info.LIQUID
            if value == 'GAS':
                value = system_info.GAS
            if value == 'ITEM':
                value = system_info.ITEM
            if type(value) is DefaultComponent:
                for class_name,class_value in self.item_list:
                    if key == class_name:
                        return class_value(**value.__dict__)
            dc.__dict__[key] = value
        if tuple_flag and 'items' in dc.to_dict():
            item = tuple(dc.to_dict()['items'])
            return item
        return dc

class DefaultComponent:
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return str(self.to_dict())

