import tcod
from tcod.console import Console
import tcod.event
from input_handler import handle_input,handle_mouse
from object import Object
import components
from part import Part
from examine_part_menu import PartMenu
from system_info import POWER,LIQUID,GAS
from json_parser import parse
import pickle
from os import getcwd,path

all_objects = {
#         'default':[
#             Part('Door', '|', fg=tcod.green, sorting_index=Part.SORTING_MAIN, blocks_gas=True, triggerable=components.Door('|', '/')),
#             Part('Wire', 7, wire=components.Connector(10, POWER), fg=tcod.yellow, sorting_index=Part.SORTING_WIRE, blocks_liquid=False, blocks_solids=False),
#             Part('Frame', ' ', sorting_index=Part.SORTING_FRAME, blocks_solids=False, blocks_liquid=False, bg=tcod.gray),
#             Part('Wall', ' ', blocks_gas=True, sorting_index=Part.SORTING_MAIN, bg=(80,80,140)),
#             Part('Generator', 'G', sorting_index=Part.SORTING_MAIN, fg=tcod.dark_red, machine=components.Machine(output=('power',1))),
#             Part('Oxygen Maker', 'M', sorting_index=Part.SORTING_MAIN, fg=tcod.dark_blue,
#                  machine=components.Machine(input=('power', 1)), liquid_machine=components.Machine(input=('water',1)), runnable=components.Runnable(components.gen_oxygen)),
#             Part('Heavy Wire', 9, wire=components.Connector(50, POWER, pipe=True), fg=tcod.yellow, sorting_index=Part.SORTING_WIRE,
#                  blocks_liquid=False, blocks_solids=False),
#             Part('Transformer', 't', network_connector=components.Transformer(5,2), fg=tcod.yellow, sorting_index=Part.SORTING_WIRE,
#                  blocks_liquid=False, blocks_solids=False),
#             Part('Switch', 's', network_connector=components.Switch(system_info=POWER), fg=tcod.light_orange, sorting_index=Part.SORTING_WIRE),
#             Part('Battery', 'b', system_storage=components.Battery(1000), fg=tcod.dark_green, sorting_index=Part.SORTING_MAIN),
#
#             Part('Liquid Pipe', ' ', liquid_pipe=components.Connector(10, LIQUID), sorting_index=Part.SORTING_LIQUID_PIPE, blocks_liquid=False, blocks_solids=False),
#             Part('Liquid Tank', 'a', system_storage=components.SystemStorage(1000, LIQUID,auto_discharge=0), fg=tcod.dark_blue, sorting_index=Part.SORTING_MAIN),
#             Part('Liquid Pump', 'p', liquid_machine=components.Machine(output=('water', 2)), fg=tcod.lightest_blue, sorting_index=Part.SORTING_MAIN, machine=components.Machine(input=('power', 1)), runnable=components.Runnable(components.default_runnable)),
#             Part('Liquid Pumper', 'u', network_connector=components.Pump(LIQUID, 5), fg=tcod.light_orange,
#                  sorting_index=Part.SORTING_LIQUID_PIPE),
#
#             Part('Gas Pipe', ' ', gas_pipe=components.Connector(10, GAS), sorting_index=Part.SORTING_GAS_PIPE, blocks_liquid=False, blocks_solids=False),
#             Part('Gas Tank', 'a', system_storage=components.SystemStorage(1000, GAS, auto_discharge=0), fg=tcod.dark_blue, sorting_index=Part.SORTING_MAIN),
#             Part('Gas Pump', 'p', gas_machine=components.Machine(output=('oxygen', 2)), fg=tcod.lightest_blue, sorting_index=Part.SORTING_MAIN),
#             Part('Gas Pumper', 'u', network_connector=components.Pump(GAS, 5), fg=tcod.light_orange, sorting_index=Part.SORTING_GAS_PIPE)
#         ]
}

object_list = []

view_dict = {
    2: lambda part: part.sorting_index == Part.SORTING_WIRE or part.power_grid,
    3: lambda part: part.sorting_index == Part.SORTING_LIQUID_PIPE or part.liquid_grid,
    4: lambda part: part.sorting_index == Part.SORTING_GAS_PIPE or part.gas_grid
}

color_view_dict = {
    2: lambda part,color: (color if not part.power_grid else (tcod.red if not part.power_grid.supplied else (tcod.orange if part.power_grid.is_stressed() else (tcod.cyan if part.power_grid.full else tcod.green)))),
    3: lambda part, color: (color if not part.liquid_grid else (tcod.red if not part.liquid_grid.supplied else (tcod.orange if part.liquid_grid.is_stressed() else (tcod.cyan if part.liquid_grid.full else tcod.green)))),
    4: lambda part, color: (color if not part.gas_grid else (tcod.red if not part.gas_grid.supplied else (tcod.orange if part.gas_grid.is_stressed() else (tcod.cyan if part.gas_grid.full else tcod.green)))),
}


def main():
    screen_width = 90
    screen_height = 60

    tcod.console_set_custom_font('terminal8x12_gs_tc.png', tcod.FONT_TYPE_GRAYSCALE | tcod.FONT_LAYOUT_TCOD)
    tcod.console_init_root(screen_width, screen_height, 'Spaceship', False, renderer=tcod.RENDERER_SDL2, vsync=True)
    tcod.console_map_ascii_code_to_font(7, 12, 2)
    tcod.console_map_ascii_code_to_font(9, 13, 2)

    object_view_width = 40
    object_view_height = 40

    main_console = Console(screen_width, screen_height, order='F')
    object_console = Console(screen_width, screen_height, order='F')

    parse(all_objects, object_list)

    frame = all_objects['base'][1]

    spaceship_x,spaceship_y = 0,0

    file_path = getcwd() + '/spaceship.dat'
    if not path.exists(file_path) or path.getsize(file_path) == 0:
        pickle.dump(Object('Spaceship', 50, 50), open(file_path, 'wb+'))

    try:
        spaceship = pickle.load(open(getcwd() + '/spaceship.dat', 'rb'))
    except pickle.UnpicklingError:
        pickle.dump(Object('Spaceship',50,50), open(file_path, 'wb+'))
        spaceship = pickle.load(open(file_path, 'rb'))


    examine_x = screen_width - 50
    examine_y = 1
    examine_width = 50
    examine_height = screen_height - 2
    examine_menu = None

    build_menu_object_key_list = ['default']

    for x in range(spaceship.width):
        for y in range(spaceship.height):
            for part in spaceship.tiles[x][y]:
                for object in object_list:
                    if not 'json_id' in part.__dict__ and object.name == part.name:
                        part.json_id = object.json_id
                        print('Assigned {} to {}'.format(part.name, object.json_id))
                    if 'json_id' in part.__dict__ and object.json_id == part.json_id:
                        part.fg = object.fg
                        part.bg = object.bg
                        part.char = object.char
                        part.sorting_index = object.sorting_index
                        part.mass = object.mass
                        break
                else:
                    print('Could not find corresponding JSON part for existing part {}'.format(part.name))


    spaceship.add_part(0,0,frame,override=True)

    spaceship.calculate_rooms()

    viewing_mode = 0
    num_modes = len(view_dict) + 2

    selection_index = 0
    max_select_index=0
    build_menu_open=False
    selection_box = (0, 0), (0, 0)

    screen_offset_x,screen_offset_y=0,0

    selection_console = Console(screen_width, screen_height, order='F')
    selection_console.clear(bg=tcod.lightest_blue)

    while True:

        response = None

        prev_select_index = selection_index
        prev_selection_coord = selection_box[0]

        for event in tcod.event.get():
            if event.type == 'KEYDOWN':
                response = {}
                input_resp = handle_input(event)
                if input_resp:
                    response.update(input_resp)
                if build_menu_open and ord('z') >= event.sym >= ord('a'):
                    response['select_item']= event.sym - ord('a')
            elif event.type == 'MOUSEBUTTONDOWN' or event.type == 'MOUSEBUTTONUP' or event.type == 'MOUSEMOTION':
                response = handle_mouse(event)
            elif event.type == 'QUIT':
                pickle.dump(spaceship, open(file_path, 'wb+'))
                return

        if response:
            if response.get('move'):
                move = response.get('move')
                if examine_menu:
                    examine_menu.selected_index += move[1]
                    if move[0] != 0:
                        if examine_menu.try_change_option(move[0]):
                            spaceship.update_all()
                else:
                    screen_offset_x = max(0, screen_offset_x + move[0])
                    screen_offset_y = max(0, screen_offset_y + move[1])
            elif response.get('viewing_mode'):
                viewing_mode = (viewing_mode + response.get('viewing_mode')) % num_modes
            elif response.get('navigate'):
                    selection_index += response.get('navigate')
                    if selection_index < 0:
                        selection_index += max_select_index
                    elif selection_index >= max_select_index:
                        selection_index -= max_select_index

            if response.get('build'):
                if not build_menu_open:
                    build_menu_open = True
                    build_menu_object_key_list = []
                    selection_index = 0
            if response.get('delete') and not build_menu_open:
                if spaceship.is_valid_coord(selection_box[0][0] - spaceship_x,
                                            selection_box[0][1] - spaceship_y) and selection_index < len(
                        spaceship.tiles[selection_box[0][0] - spaceship_x][selection_box[0][1] - spaceship_y]):
                    part_name = spaceship.tiles[selection_box[0][0]-spaceship_x][selection_box[0][1]-spaceship_y][selection_index].name
                    for x in range(selection_box[0][0], selection_box[1][0]):
                        for y in range(selection_box[0][1], selection_box[1][1]):
                            for part in spaceship.tiles[x][y]:
                                if part.name == part_name:
                                    spaceship.remove_part(x - spaceship_x, y - spaceship_y,
                                                part)
            elif (response.get('select') or response.get('mouse_move_lheld') or response.get('lclick_down')) and build_menu_open:
                if type(get_object(build_menu_object_key_list)) is list:
                    if response.get('mouse_move_lheld'):
                        selection_box = response.get('mouse_move_lheld'),(response.get('mouse_move_lheld')[0] + 1, response.get('mouse_move_lheld')[1] + 1)
                    for x in range(selection_box[0][0], selection_box[1][0]):
                        for y in range(selection_box[0][1], selection_box[1][1]):
                            spaceship.add_part(x - spaceship_x, y - spaceship_y,
                                       get_object(build_menu_object_key_list)[selection_index])
                else:
                    build_menu_object_key_list.append(list(get_object(build_menu_object_key_list).keys())[selection_index])
                    selection_index = 0
            elif response.get('run'):
                for x in range(spaceship.width):
                    for y in range(spaceship.height):
                        for part in [part for part in spaceship.tiles[x][y] if part.runnable]:
                            part.runnable.run(spaceship, part, x, y)
                spaceship.update_all()

            if response.get('rclick_down'):
                selection_box = response.get('rclick_down'),response.get('rclick_down')
            elif response.get('lclick_down'):
                selection_box = response.get('lclick_down'), response.get('lclick_down')
            elif response.get('mouse_move_rheld'):
                selection_box = selection_box[0],(response.get('mouse_move_rheld')[0] + 1, response.get('mouse_move_rheld')[1] + 1)
            elif response.get('mouse_move') and selection_box[1][0] - selection_box[0][0] <= 1 and selection_box[1][1] - selection_box[0][1] <= 1:
                selection_box = response.get('mouse_move'),(response.get('mouse_move')[0] + 1, response.get('mouse_move')[1] + 1)
            elif response.get('select_item') is not None:
                index = response.get('select_item')
                if index < max_select_index:
                    selection_index = index

                    if type(get_object(build_menu_object_key_list)) is dict:
                        build_menu_object_key_list.append(list(get_object(build_menu_object_key_list).keys())[selection_index])
                        selection_index = 0

            if response.get('escape'):
                if build_menu_open:
                    if len(build_menu_object_key_list) == 0:
                        build_menu_open = False
                        selection_index = 0
                    else:
                        build_menu_object_key_list.pop(-1)
                elif examine_menu:
                    examine_menu = None

        if prev_select_index != selection_index or prev_selection_coord != selection_box[0]:
            if spaceship.is_valid_coord(selection_box[0][0] - spaceship_x,
                                        selection_box[0][1] - spaceship_y) and selection_index < len(
                    spaceship.tiles[selection_box[0][0] - spaceship_x][selection_box[0][1] - spaceship_y]):
                examine_menu = PartMenu(spaceship,
                    spaceship.tiles[selection_box[0][0] - spaceship_x][selection_box[0][1] - spaceship_y][
                        selection_index], examine_width, examine_height, selection_box[0][0], selection_box[0][1])
            else:
                examine_menu = None


        tcod.console_flush()
        main_console.clear(bg=tcod.black)

        selection_pos = selection_box[0]

        object_console.clear()
        render_object(object_console, spaceship, spaceship_x, spaceship_y, viewing_mode)

        object_console.blit(main_console, 0, 0, screen_offset_x, screen_offset_y, object_view_width, object_view_height)

        # main_console.put_char(selection_box[0][0], selection_box[0][1], ord('X'))
        # main_console.fg[selection_box[0][0], selection_box[0][1]] = tcod.cyan
        if build_menu_open:
            iterable = get_object(build_menu_object_key_list)
            if type(iterable) is list:
                iterable = [item.name for item in iterable]
            else:
                iterable = [item.capitalize() for item in iterable]
            for i in range(len(iterable)):
                main_console.print(screen_width-50,i,chr(ord('a') + i) + ' - ' + iterable[i],bg=(tcod.desaturated_blue if selection_index == i else tcod.black))
                main_console.fg[screen_width-50,i] = tcod.light_green
            max_select_index = len(iterable)
        else:
            main_console.print(0, screen_height-1,str(viewing_mode))
            if spaceship_x <= selection_pos[0] < spaceship_x + spaceship.width and spaceship_y <= selection_pos[1] < spaceship_y + spaceship.height:
                room = spaceship.find_room(selection_pos[0] - spaceship_x, selection_pos[1]-spaceship_y)
                parts = [part for part in spaceship.tiles[selection_pos[0]-spaceship_x][selection_pos[1]-spaceship_y]]
                if room:
                    gas_y = len(parts)+2
                    for gas in room.gas_content:
                        main_console.print(20,gas_y,'{1}: {0:.2f} kPa'.format(components.calc_pressure(room.gas_content[gas], len(room.tiles)), gas.capitalize()))
                        gas_y += 1
                for i in range(len(parts)):
                    part = parts[i]
                    string = part.name

                    if part.gas_grid:
                        string += ' {}'.format(part.gas_grid.index)

                    main_console.print(20,i+1,string,bg=(tcod.desaturated_blue if selection_index == i else tcod.black))
                max_select_index = len(parts)

            if examine_menu:
                examine_menu.draw()
                examine_menu.console.blit(main_console, examine_x, examine_y, 0, 0, examine_width, examine_height)

        dsel_x = selection_box[1][0] - selection_box[0][0]
        dsel_y = selection_box[1][1] - selection_box[0][1]

        if dsel_x > 0 and dsel_y > 0:
            selection_console.blit(main_console, selection_box[0][0], selection_box[0][1],0,0,dsel_x, dsel_y, bg_alpha=0.25)

        main_console.blit(tcod.console._root_console, width=screen_width, height=screen_height, bg_alpha=1)


def render_object(console, object, x_offset, y_offset, viewing_mode):

    if viewing_mode == 0:
        x = 0
        y = 0
        for x_list in object.tiles:
            y = 0
            for part_list in object.tiles[x]:
                for part in part_list:
                    if part.sorting_index <= Part.SORTING_MAIN:
                        char,fg,bg = part.get_render(object, x, y)
                        console.put_char(x + x_offset, y + y_offset, char)
                        console.fg[x + x_offset, y + y_offset] = fg
                        if bg is not None:
                            console.bg[x + x_offset, y + y_offset] = bg
                y += 1
            x += 1
    elif viewing_mode == 1:
        for room in object.gas_rooms:
            color = tcod.red if room.exposed else (tcod.orange if room.calc_pressure() == 0 else tcod.color_lerp(tcod.darkest_blue, tcod.lighter_blue, room.calc_pressure()/120))
            for coord in room.tiles:
                console.put_char(coord[0] + x_offset, coord[1] + y_offset, ord(' '))
                console.bg[coord[0] + x_offset, coord[1] + y_offset] = color
    elif 2 <= viewing_mode <= 8:
        if viewing_mode in view_dict:
            x = 0
            y = 0
            for x_list in object.tiles:
                y = 0
                for part_list in object.tiles[x]:
                    if len(part_list) > 0:
                        char,fg,bg = part_list[-1].get_render(object, x, y)
                        fg = tcod.light_gray
                        bg = None
                        for part in reversed(part_list):
                            new_char,new_fg,new_bg = part.get_render(object, x, y)
                            if view_dict[viewing_mode](part):
                                char, fg = new_char,new_fg
                                if viewing_mode in color_view_dict:
                                    fg = color_view_dict[viewing_mode](part, fg)
                            else:
                                if char == ' ' or char == '':
                                    char = new_char
                                if new_bg and not bg:
                                    if part.sorting_index != Part.SORTING_FRAME:
                                        bg = tcod.darker_gray
                                    else:
                                        bg = new_bg

                        if fg is not None:
                            console.put_char(x + x_offset, y + y_offset, char)
                            console.fg[x + x_offset, y + y_offset] = fg
                        if bg is not None:
                            console.bg[x + x_offset, y + y_offset] = bg
                    y += 1
                x += 1

def get_object(list_of_keys):
    dct = all_objects
    for key in list_of_keys:
        dct = dct[key]
    return dct


if __name__ == '__main__':
    main()