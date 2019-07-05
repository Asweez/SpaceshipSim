import tcod.event as tevent

def handle_input(event):
    if event.sym == tevent.K_UP:
        return {'move':(0,-1)}
    if event.sym == tevent.K_DOWN:
        return {'move':(0,1)}
    if event.sym == tevent.K_RIGHT:
        return {'move':(1,0)}
    if event.sym == tevent.K_LEFT:
        return {'move':(-1,0)}

    if event.sym == tevent.K_EQUALS:
        return {'viewing_mode':1}
    if event.sym == tevent.K_MINUS:
        return {'viewing_mode':-1}
    if event.sym == tevent.K_RETURN:
        return {'select':True}
    if event.sym == tevent.K_BACKSPACE:
        return {'delete':True}
    if event.sym == tevent.K_ESCAPE:
        return {'escape':True}
    if event.sym == tevent.K_a:
        return {'build':True}
    if event.sym == tevent.K_e:
        return {'examine':True}

    if event.sym == tevent.K_LEFTBRACKET:
        return {'navigate':-1}
    if event.sym == tevent.K_RIGHTBRACKET:
        return {'navigate':1}

    if event.sym == tevent.K_r:
        return {'run':True}

    if event.sym == tevent.K_o:
        return {'open_doors':True}

    return None

def handle_mouse(event):
    if event.type == 'MOUSEBUTTONDOWN' and event.button == tevent.BUTTON_RIGHT:
        return {'rclick_down':event.tile}
    if event.type == 'MOUSEBUTTONDOWN' and event.button == tevent.BUTTON_LEFT:
        return {'lclick_down':event.tile}
    if event.type == 'MOUSEBUTTONUP' and event.button == tevent.BUTTON_RIGHT:
        return {'rclick_up':event.tile}
    if event.type == 'MOUSEMOTION':
        if event.state & tevent.BUTTON_RMASK:
            return {'mouse_move_rheld':event.tile}
        elif event.state & tevent.BUTTON_LMASK:
            return {'mouse_move_lheld':event.tile}
        else:
            return {'mouse_move':event.tile}

    return None