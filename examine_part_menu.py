from tcod.console import Console
from part import BaseComponent
import tcod

class PartMenu:

    def __init__(self, object, part, width, height, x, y):
        self.object = object
        self.part = part
        self.width = width
        self.height = height
        self.console = Console(width, height)
        self.selected_index = 0
        self.x = x
        self.y = y

    def draw(self):

        #format: key=option name, value = (list of options, selected_option)
        options = {}

        self.console.clear()

        x = 0
        y = 2

        self.console.print(x, 0, 'Examining: ' + self.part.name)

        index = 0
        for component in self.part.components:
            if component in self.part.__dict__ and self.part.__dict__[component] and isinstance(self.part.__dict__[component], BaseComponent):
                part_component = self.part.__dict__[component]
                y += self.console.print_box(x, y, self.width, self.height - y, part_component.get_desc(), fg=tcod.gray)
                component_options = part_component.get_options(self.part)
                for option_name,(part_options, selected_option) in component_options.items():
                    self.console.print(x,y,option_name, bg=(tcod.desaturated_green if index == self.selected_index else tcod.black))
                    x += len(option_name) + 1
                    for i in range(len(part_options)):
                        if x >= self.width:
                            x = 0
                            y += 1
                        part_option = part_options[i]
                        self.console.print(x,y,part_option, bg=(tcod.desaturated_blue if i == selected_option else tcod.black))
                        x += len(part_option) + 1
                    index += 1
                    x = 0
                    y += 1
        if index == 0:
            self.selected_index = 0
        else:
            self.selected_index = self.selected_index % index

    def try_change_option(self, change):
        index = 0
        for component in self.part.components:
            if self.part.__dict__[component] and isinstance(self.part.__dict__[component], BaseComponent):
                part_component = self.part.__dict__[component]
                component_options = part_component.get_options(self.part)
                for option_name,(part_options, selected_option) in component_options.items():
                    if index == self.selected_index:
                        selected_option = (selected_option + change) % len(part_options)
                        part_component.change_option(option_name, selected_option, self.part, self.object, self.x, self.y)
                        return True
                    index += 1

        return False


