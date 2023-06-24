import pygame, random, math, time, sys, os, copy, pygame.gfxdraw

""" TODO
 - main menu
     - settings
         - add optional image param for selected, non-selected, true, false, etc.
         - zoom amount
         - power ups
         - default settings
         - hide settings at end of image
 - power ups
     - make more bullet
     - ender pearl
     - spinning thing that if hits bullet then acts as shield
     - bullet teleporter
     - planet destroyer
     - planet surface base for shooting down bullets
     - double points on kill
     - gravity randomizer
     - spawn new planet
 - performance issues (draw all to as few surfaces as possible)
     - same thing for players but every turn switch
     - same for the score indication
     - game control class that determines what is getting updated
 - funny discord networking
 - fix
     - fix bullet trail not working for split bullets
     - screen flicker on generation
 - make planet generation weighted so that inside and just outside even but decrease after
     - after certain range rand + rand/2
"""

screen_width, screen_height = 1280, 720
d_time = 0
world_speed = 1
pixels_per_meter = 200
#stop_vel = (1*pixels_per_meter)/2

pass_by_reference_list = []

camera_scale_zoomed = 1/3

camera_scale = 1
camera_offset = [0, 0]

PLAYER_SCORES = []
CURR_PLAYER = 0

explode_img = pygame.transform.scale( pygame.image.load('explode.png'), (pygame.image.load('player.png').get_size()))

#G_CONST = 0.0000000000066743
#1080
G_CONST = 1110
REMAINING_PLAYERS = 0

players = []
planets = []
bullets = []
powerups = []

text_size = 16
myfont = None

def str_to_type(x):
    try:
        #print(x)
        if x == "True":
            return True
        elif x == "False":
            return False
    except:
        pass
    try:
        return int(x)
    except:
        pass
    try:
        return float(x)
    except:
        pass
    return x

class named_value():
    def __init__(self, value, filename, settings_value_list=None):
        self.value = value
        self.filename = filename

        name = filename
        name = name.lower()
        if len(name) > 0:
            name = name.capitalize()
        for i in range(len(name)):
            if name[i] == '_':
                name = name[:i] + ' ' + name[i+1:].capitalize()
        self.name = name

        if settings_value_list != None:
            settings_value_list.append(self)


''' settings '''

'''GENERATE_OUTSIDE = False
NUM_PLAYERS = 2
MIN_PLANETS = 3
MAX_PLANETS = 5
BULLET_TIMEOUT = 20'''

settings_value_list = []

GENERATE_OUTSIDE = named_value(False, "GENERATE_OUTSIDE", settings_value_list)
NUM_PLAYERS = named_value(2, "NUM_PLAYERS", settings_value_list)
MIN_PLANETS = named_value(3, "MIN_PLANETS", settings_value_list)
MAX_PLANETS = named_value(5, "MAX_PLANETS", settings_value_list)
BULLET_TIMEOUT = named_value(20, "BULLET_TIMEOUT", settings_value_list)
NUM_POWERUPS = named_value(0, "NUM_POWERUPS", settings_value_list)
'''   end    '''

settings_filename = 'space_bg0.png'
in_file = None
if os.path.exists(settings_filename):
    in_file = open(settings_filename, 'r')
else:
    out_file = open(settings_filename, 'w')
    out_file.close()
    in_file = open(settings_filename, 'r')

#GENERATE_OUTSIDE=False\nNUM_PLAYERS=2

for line in in_file.readlines():
    var_name = line[:line.find('=')]
    for e in settings_value_list:
        if var_name == e.filename:
            e.value = str_to_type(line[line.find('=')+1:-1])

in_file.close()

class power_up():
    def __init__(self, pos, color=None, size=None):
        self.pos = pos
        self.color = color
        self.size = size
        self.cool_down = 750*1000000
        self.last_use = time.time_ns()

    def collide(self, s):
        #print(f"{distance(self.pos, s.pos)} <= {s.size[0]/2 + self.size[0]/2}")
        return (distance(self.pos, s.pos) <= s.size[0]/2 + self.size[0]/2)

    def update(self):
        pass

    def draw(self, surf):
        global camera_offset, camera_scale, camera

        pygame.draw.ellipse(surf, self.color, ((self.pos[0] - self.size[0]/2)*camera_scale + camera_offset[0], (to_screen_pos(self.pos)[1] - self.size[1]/2)*camera_scale + camera_offset[1], self.size[0]*camera_scale, self.size[1]**camera_scale))

        '''if camera.scaled:
            temp = to_screen_pos([self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1]/2])
            pygame.draw.ellipse(surf, self.color, (temp[0], temp[1], self.size[0]*camera_scale, self.size[1]*camera_scale))
        else:
            pygame.draw.ellipse(surf, self.color, (self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1]/2, self.size[0], self.size[1]))'''

class power_up_bullet_split(power_up):
    def __init__(self, pos, color=None, size=None):
        super().__init__(pos, color, size)

    def update(self):
        global bullets

        if time.time_ns() > self.last_use + self.cool_down:
            #print()
            for b in bullets:
                if self.collide(b):
                    #def __init__(self, size, color, pos, vel, color2, owner, timed_out=None):
                    bullets.append(bullet(b.size, b.color, copy.copy(b.pos), vec_calc(vec_h(copy.copy(b.vel)), vec_to_angle(copy.copy(b.vel)) + 15), (b.color2[0], b.color2[1], b.color2[2], 75), b.owner, True))
                    bullets.append(bullet(b.size, b.color, copy.copy(b.pos), vec_calc(vec_h(copy.copy(b.vel)), vec_to_angle(copy.copy(b.vel)) - 15), (b.color2[0], b.color2[1], b.color2[2], 75), b.owner, True))
                    self.last_use = time.time_ns()
                    break

class menu_element():
    def __init__(self, ref_var):
        #global pass_by_reference_list

        self.text = ref_var.name

        #surf
        '''self.t_unselected = None
        self.t_selected = None
        self.t_true = None
        self.t_false = None'''

        #pass_by_reference_list.append(ref_var)
        self.ref_var = ref_var

    def get_texture(self, font_render, selected):
        hc = None
        if selected:
            hc = (100, 100, 100)
        else:
            hc = (0, 0, 0)

        return font_render.render(self.text, True, (255, 255, 255), hc)

    def left(self):
        pass
    def right(self):
        pass

    def select(self):
        pass

class menu_control(menu_element):
    def __init__(self, element_gap, text_size, ref_var=named_value(None, "")):
        super().__init__(ref_var)
        self.element_gap = element_gap
        self.text_size = text_size
        self.elements = []
        self.alpha = 5
        self.ref_var = ref_var

        self.text = ref_var.name

        self.menu_selected = None

        self.index = 0

    def add_element(self, e):
        if isinstance(e, menu_control):
            #pass_by_reference_list.append(e)
            #self.ref_var = len(pass_by_reference_list)-1
            self.elements.append(e)
            return e
        self.elements.append(e)
        return e.ref_var

    def down(self):
        if self.menu_selected:
            self.elements[self.menu_selected].down()
        else:
            self.index += 1
            if self.index >= len(self.elements):
                self.index = len(self.elements)-1
    def up(self):
        if self.menu_selected:
            self.elements[self.menu_selected].up()
        else:
            self.index -= 1
            if self.index < 0:
                self.index = 0

    def select_right(self):
        if self.menu_selected:
            self.elements[self.menu_selected].select_right()
        else:
            self.elements[self.index].right()
    def select_left(self):
        if self.menu_selected:
            self.elements[self.menu_selected].select_left()
        else:
            self.elements[self.index].left()

    def select_element(self):
        if self.menu_selected:
            self.elements[self.menu_selected].select_element()
        else:
            self.elements[self.index].select()
            if isinstance(self.elements[self.index], menu_control):
                self.menu_selected = self.index

    def exit_menu(self):
        if self.menu_selected:
            if self.elements[self.menu_selected].menu_selected:
                self.elements[self.menu_selected].exit_menu()
            else:
                self.menu_selected = None
        else:
            return

    def draw(self, surf):
        global screen_width, screen_height

        if self.menu_selected:
            if isinstance(self.elements[self.menu_selected], menu_control):
                self.elements[self.menu_selected].draw(surf)
        else:
            real_i = 0
            for i in range(len(self.elements)):
                e = self.elements[i]
                if e.text:
                    '''if hasattr(e, 'text'):
                        print("yes")
                    else:
                        print("no")'''

                    font_render = pygame.font.SysFont('arial', self.text_size)
                    t = e.get_texture(font_render, real_i == self.index)

                    #pygame.draw.rect(surf, (0, 0, 0, 100), (screen_width/2 - t.get_size()[0]/2, len(self.elements)))
                    surf.blit(t, (screen_width/2 - t.get_size()[0]/2, screen_height/2 - len(self.elements)*(t.get_size()[1] + self.element_gap)/2 + real_i*(t.get_size()[1] + self.element_gap) - self.element_gap))

                    real_i += 1

class menu_element_save(menu_element):
    def __init__(self, ref_var):
        super().__init__(ref_var)

    def select(self):
        global settings_filename, settings_value_list

        final = ""
        in_file = open(settings_filename, 'r')

        for e in settings_value_list:
            final += e.filename + "=" + str(e.value) + "\n"

        for line in in_file.readlines():
            var_name = line[:line.find('=')]
            wasnt_element = True
            for e in settings_value_list:
                if var_name == e.filename:
                    wasnt_element = False
                    break
            if wasnt_element:
                final += line

        in_file.close()
        out_file = open(settings_filename, 'w')
        out_file.write(final)
        out_file.close()

class menu_element_bool(menu_element):
    def __init__(self, ref_var):
        super().__init__(ref_var)

    def get_texture(self, font_render, selected):
        hc = None
        if selected:
            if self.ref_var.value:
                hc = (0, 200, 0)
            else:
                hc = (200, 0, 0)
        else:
            if self.ref_var.value:
                hc = (0, 100, 0)
            else:
                hc = (100, 0, 0)

        return font_render.render(self.text, True, (255, 255, 255), hc)

    def left(self):
        self.ref_var.value = False
    def right(self):
        self.ref_var.value = True

    def select(self):
        #global pass_by_reference_list
        self.ref_var.value = not self.ref_var.value

class menu_element_int(menu_element):
    def __init__(self, ref_var):
        super().__init__(ref_var)

    def get_texture(self, font_render, selected):
        hc = None
        if selected:
            hc = (100, 100, 100)
        else:
            hc = (0, 0, 0)

        return font_render.render(self.text + ": " + str(self.ref_var.value), True, (255, 255, 255), hc)

    def left(self):
        #global pass_by_reference_list
        self.ref_var.value -= 1
        if self.ref_var.value < 0:
            self.ref_var.value = 0
    def right(self):
        #global pass_by_reference_list
        self.ref_var.value += 1
    def select(self):
        pass

def randcolor_bright():
    c = [random.random()*256, random.random()*256, random.random()*256]
    s = c.copy()
    s.sort()
    #print()
    #print(c)
    diff = 255 - s[-1]
    #print(diff)
    for i in range(len(c)):
        c[i] += diff
    c = (int(c[0]), int(c[1]), int(c[2]))
    #print(c)
    return c

class drift_controller():
    def __init__(self, min_pos1, max_pos1, start, speed):
        self.min_pos = [(min_pos1[0] - max_pos1[0])/2.0, (min_pos1[1] - min_pos1[1])/2.0]
        self.max_pos = [(min_pos1[0] - max_pos1[0])/2.0 + max_pos1[0], (min_pos1[0] - max_pos1[0])/2.0 + max_pos1[0]]
        self.speed = speed
        self.angle = random.random()*360
        self.pos = start
        self.offset = [self.min_pos[0] - min_pos1[0], self.min_pos[1] - min_pos1[1]]

    def update(self):
        global d_time

        if self.angle < 0:
            self.angle += 360
        elif self.angle > 360:
            self.angle -= 360

        weight1 = abs(self.pos[0]/self.max_pos[0])
        weight2 = abs(self.pos[1]/self.max_pos[1])

        weight = 0
        if weight1 > weight2:
            weight = weight1
        else:
            weight = weight2

        #print(weight)

        self.angle = vec_to_angle([self.pos[0]*-1, self.pos[1]*-1])*(weight) + self.angle*(1-weight)
        #print(self.angle)

        vel = vec_calc(self.speed, self.angle)
        self.pos[0] += vel[0]
        self.pos[1] += vel[1]

        return (self.pos[0] + self.offset[0], self.pos[1] + self.offset[1])

class camera_controller():
    def __init__(self):
        self.zoom_press = False
        self.scaled = False
        #self.edge_gap = 200*2

    def zoom_out_point(self, p):
        camera_scale = camera_scale_zoomed
        camera_offset = [screen_width*camera_scale, screen_height*camera_scale]

        return [p[0]*camera_scale + camera_offset[0], ((p[1]) - screen_height)*-1*camera_scale + camera_offset[1]]

    def zoom_in(self):
        global camera_scale, camera_offset
        camera_scale = 1
        camera_offset = [0, 0]

    def zoom_out(self):
        global screen_width, screen_height, camera_offset, camera_scale, camera_scale_zoomed
        camera_scale = camera_scale_zoomed
        camera_offset = [screen_width*camera_scale, screen_height*camera_scale]

    def update(self, bullets):
        global screen_width, screen_height, camera_offset, camera_scale

        self.scaled = True

        #print("w")

        for b in bullets:
            if not b.timed_out:
                if b.pos[0] < 0 or b.pos[0] > screen_width or b.pos[1] < 0 or b.pos[1] > screen_height:
                    self.zoom_out()
                    return

        #if len(bullets) >= 1:
        #    camera_scale = 1.000001
        #    camera_offset = [bullets[0].pos[0]*camera_scale*-1 + screen_width/2, bullets[0].pos[1]*camera_scale - screen_height/2]
        #    return

        if self.zoom_press:
            self.zoom_out()
            return

        self.scaled = False
        #print("h")
        camera_scale = 1
        camera_offset = [0, 0]

    def keyup_zoom(self):
        self.zoom_press = False

    def keydown_zoom(self):
        self.zoom_press = True

camera = camera_controller()

def vec_h(v):
    return math.sqrt(v[0]**2 + v[1]**2)

def vec_calc(h, angle):
    ang = angle*math.pi/180
    fvec = [0, 0]
    fvec[1] = math.sin(ang)*h
    fvec[0] = math.cos(ang)*h

    return fvec

#for i in range(int(360/45) + 1):
#    print(str(i*45) + ": " + str(vec_calc(1, i*45)))

def vec_to_angle(a):
    value = math.atan2(a[1], a[0])*(180/math.pi)
    if value < 0:
        value += 360
    return value

#for i in range(int(360/15)):
#    print("\n" + str(i*15))
#    print(vec_calc(1, i*15))
#    print(vec_to_angle(vec_calc(1, i*15)))

def distance(l1, l2):
    x, y = l1
    x2, y2 = l2
    return math.sqrt(abs(x2 - x)**2 + abs(y2-y)**2)

def pixel_cord_to_meters(pos):
    global pixels_per_meter, screen_width, screen_height

    #(abs(pos[1]-screen_height) - self.size[1])/pixels_per_meter

    return ((abs(pos[0]-screen_width))/pixels_per_meter, (abs(pos[1]-screen_height))/pixels_per_meter)

class bullet():
    global pixels_per_meter, screen_height

    def __init__(self, size, color, pos, vel, color2, owner, timed_out=None):
        self.size = size
        self.color = color
        self.pos = pos
        self.vel = vel*pixels_per_meter
        #self.acc = [0, 0]*pixels_per_meter
        self.time = 0
        self.start_h = pos[1]
        self.stop = False
        #(100, 100, 100)
        self.color2 = color2
        self.color3 = (color2[0], color2[1], color2[2], 150)
        self.last_pos = pos

        self.owner = owner
        self.timed_out = False
        if timed_out:
            self.timed_out = timed_out
        self.time_fired = time.time_ns()

        self.mass = size[0]/2*size[1]/2*math.pi

    def collide(self, s):
        return (distance(self.pos, s.pos) <= s.size[0]/2 + self.size[0]/2)

    def update(self, planets, bullets):
        global d_time, screen_height, screen_width, G_CONST, BULLET_TIMEOUT, players, game

        self.last_pos = [self.pos[0], self.pos[1]]

        if not self.timed_out:
            if time.time_ns() > self.time_fired + BULLET_TIMEOUT.value:
                self.timed_out = True
                game.next_turn()

        #f=ma

        for p in planets:
            if self.collide(p):
                if not self.timed_out:
                    game.next_turn()
                    #players[self.owner].firing = False
                bullets.remove(self)
                return

            tempVec = vec_calc((G_CONST*((self.mass * p.mass)/(distance(self.pos, p.pos)**2))), vec_to_angle([p.pos[0] - self.pos[0], p.pos[1] - self.pos[1]]))
            self.vel[0] += tempVec[0]/self.mass*d_time
            self.vel[1] += tempVec[1]/self.mass*d_time
            #print([tempVec[0]/self.mass*d_time, tempVec[1]/self.mass*d_time])

        #self.vel[0] += 0*d_time
        #self.vel[1] += 0*d_time

        self.pos[0] += self.vel[0]*d_time
        self.pos[1] += self.vel[1]*d_time

        if self.pos[0] < screen_width*-1:
            if not self.timed_out:
                    game.next_turn()
            bullets.remove(self)
        elif self.pos[0] > screen_width*2:
            if not self.timed_out:
                    game.next_turn()
            bullets.remove(self)
        elif self.pos[1] > screen_height*2:
            if not self.timed_out:
                    game.next_turn()
            bullets.remove(self)
        elif self.pos[1] < screen_height*-1:
            if not self.timed_out:
                    game.next_turn()
            bullets.remove(self)

    def draw(self, surf, screen_bullet_trail, screen_bullet_trail2):
        global camera_scale, camera_offset, myfont, text_size, screen_width, BULLET_TIMEOUT, camera, players

        #pygame.draw.line(screen_bullet_trail, self.color2, to_screen_pos2(self.last_pos), to_screen_pos2(self.pos))

        pygame.draw.line(screen_bullet_trail, self.color2, to_screen_pos(self.last_pos), to_screen_pos(self.pos))
        pygame.draw.line(screen_bullet_trail2, self.color2, camera.zoom_out_point(self.last_pos), camera.zoom_out_point(self.pos))

        '''x0 = to_screen_pos(self.last_pos)
        x1 = to_screen_pos(self.pos)
        pygame.gfxdraw.line(screen_bullet_trail, int(x0[0]), int(x0[1]), int(x1[0]), int(x1[1]), self.color2)
        x0 = camera.zoom_out_point(self.last_pos)
        x1 = camera.zoom_out_point(self.pos)
        pygame.gfxdraw.line(screen_bullet_trail2, int(x0[0]), int(x0[1]), int(x1[0]), int(x1[1]), self.color3)'''

        if not self.timed_out:
            pygame.draw.line(players[self.owner].screen_highlight_1, (255, 255, 255), to_screen_pos(self.last_pos), to_screen_pos(self.pos))
            pygame.draw.line(players[self.owner].screen_highlight_2, (255, 255, 255), camera.zoom_out_point(self.last_pos), camera.zoom_out_point(self.pos))

            tempSurf = myfont.render("Timeout: " + "{:.2f}". format((BULLET_TIMEOUT.value - (time.time_ns() - self.time_fired))/1000000000), True, (255, 255, 255), (0, 0, 0))

            surf.blit(tempSurf, (screen_width/2 - tempSurf.get_size()[0]/2, 10))

        pygame.draw.ellipse(surf, self.color2, ((self.pos[0] - self.size[0]/2)*camera_scale + camera_offset[0], (to_screen_pos(self.pos)[1] - self.size[1]/2)*camera_scale + camera_offset[1], self.size[0], self.size[1]))

def to_screen_pos(p):
    global screen_height
    return [p[0], ((p[1]) - screen_height)*-1]

def to_screen_pos2(p):
    global screen_height, camera_scale, camera_offset
    return [p[0]*camera_scale + camera_offset[0], ((p[1]) - screen_height)*-1*camera_scale + camera_offset[1]]

class planet():
    global pixels_per_meter

    def __init__(self, img, size, pos):
        self.img = pygame.transform.scale(img, size)
        self.size = size
        self.pos = pos

        self.mass = size[0]/2*size[1]/2*math.pi

    def draw(self, surf):
        global camera_scale, camera_offset
        #print((self.pos[0] - self.img.get_size()[0]/2, to_screen_pos(self.pos)[1] - self.img.get_size()[1]/2))

        #pygame.draw.ellipse(surf, (255, 255, 255), (to_screen_pos2(self.pos)[0] - self.img.get_size()[0]/2*camera_scale, to_screen_pos2(self.pos)[1] - self.img.get_size()[1]/2*camera_scale, self.size[0]*camera_scale, self.size[1]*camera_scale))

        if camera_scale == 1:
            surf.blit(self.img, (self.pos[0] - self.img.get_size()[0]/2, to_screen_pos(self.pos)[1] - self.img.get_size()[1]/2))
        else:
            #print("h")
            tempSurf = pygame.transform.rotozoom( self.img, 0, camera_scale)
            surf.blit(tempSurf, (to_screen_pos2(self.pos)[0] - self.img.get_size()[0]/2*camera_scale, to_screen_pos2(self.pos)[1] - self.img.get_size()[1]/2*camera_scale))

class player():
    global pixels_per_meter

    def __init__(self, img, color, angle, power, pos, index):
        self.color = color
        self.img = tint(img, color)
        self.angle = angle
        self.power = power*pixels_per_meter
        self.anlge_speed = 60
        self.power_speed = 150
        self.pos = pos
        self.size = distance((0, 0), img.get_size())
        self.alive = True

        self.lowsens_multiplier = 1/3.0
        self.lowsens = False

        self.screen_highlight_1 = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        self.screen_highlight_2 = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)

        self.index = index

        self.turning_left = False
        self.turning_right = False

        self.powup = False
        self.powdown = False

        self.firing = False

    def collide(self, s):
        if (distance(self.pos, s.pos) <= self.size/2):
            return True
        return False

    def start_left(self):
        self.turning_left = True
    def stop_left(self):
        self.turning_left = False
    def start_right(self):
        self.turning_right = True
    def stop_right(self):
        self.turning_right = False

    def start_powup(self):
        self.powup = True
    def stop_powup(self):
        self.powup = False
    def start_powdown(self):
        self.powdown = True
    def stop_powdown(self):
        self.powdown = False

    def start_sensdown(self):
        self.lowsens = True
    def stop_sensdown(self):
        self.lowsens = False

    def end_turn(self):
        self.turning_left = False
        self.turning_right = False

        self.powup = False
        self.powdown = False

    def update(self, bullets, players):
        global explode_img, PLAYER_SCORES, CURR_PLAYER, REMAINING_PLAYERS
        for b in bullets:
            if self.collide(b):

                self.img = explode_img
                if self.alive:
                    REMAINING_PLAYERS -= 1
                    if b.owner == self.index:
                        PLAYER_SCORES[CURR_PLAYER] -= 1
                    else:
                        PLAYER_SCORES[CURR_PLAYER] += 1
                self.alive = False
                if not b.timed_out:
                    game.next_turn()
                bullets.remove(b)

        if self.firing:
            self.turning_left = False
            self.turning_right = False
            self.powup = False
            self.powdown = False
        else:
            if self.turning_left:
                self.turn_left()
            if self.turning_right:
                self.turn_right()

            if self.powup:
                self.pow_up()
            if self.powdown:
                self.pow_down()

    def pow_up(self):
        global d_time

        self.power += self.power_speed*d_time*(self.lowsens_multiplier if self.lowsens else 1)
        if self.power > 625:
            self.power = 625

    def pow_down(self):
        global d_time

        self.power -= self.power_speed*d_time*(self.lowsens_multiplier if self.lowsens else 1)
        if self.power < 10:
            self.power = 10

    def turn_left(self):
        global d_time

        self.angle += self.anlge_speed*d_time*(self.lowsens_multiplier if self.lowsens else 1)
        if self.angle > 360:
            self.angle -= 360

    def turn_right(self):
        global d_time

        self.angle -= self.anlge_speed*d_time*(self.lowsens_multiplier if self.lowsens else 1)
        if self.angle < 0:
            self.angle += 360

    def shoot(self, bullets):
        #print(self.angle)
        self.lowsens = False
        if not self.firing:
            self.screen_highlight_1.fill(0)
            self.screen_highlight_2.fill(0)
            bullets.append(bullet((5, 5), (255, 0, 0), [self.pos[0] + vec_calc(self.size, self.angle)[0], self.pos[1] + vec_calc(self.size, self.angle)[1]], vec_calc(self.power, self.angle), self.color, self.index))
        self.firing = True

    def draw(self, surf):
        global camera_scale, camera_offset, CURR_PLAYER
        tempSurf = pygame.transform.rotozoom(self.img, self.angle - 90, camera_scale)
        #print()
        #tempSurf.get_size()[1]/2
        surf.blit(tempSurf, ((self.pos[0] - tempSurf.get_size()[0]/2)*camera_scale + camera_offset[0], ((to_screen_pos((0, self.pos[1]))[1] - tempSurf.get_size()[1]/2))*camera_scale + camera_offset[1]))

        tempVec = vec_calc(self.power/3, self.angle)

        if CURR_PLAYER == self.index:
            if camera.scaled:
                surf.blit(self.screen_highlight_2, (0, 0))
            else:
                surf.blit(self.screen_highlight_1, (0, 0))
            pygame.draw.line(surf, (255, 255, 255), to_screen_pos2(self.pos), to_screen_pos2((self.pos[0] + tempVec[0], self.pos[1] + tempVec[1])))


def tint(surf, tint_color):
    """ adds tint_color onto surf.
    """
    surf = surf.copy()
    # surf.fill((0, 0, 0, 255), None, pygame.BLEND_RGBA_MULT)
    surf.fill(tint_color[0:3] + (0,), None, pygame.BLEND_RGBA_ADD)
    return surf

def tint2(surf, tint_color):
    surf = surf.copy()
    surf.fill((0, 0, 0, tint_color), None, pygame.BLEND_RGBA_SUB)
    return surf

class game_controller():
    def __game_controller__():
        pass

    def next_turn(self):
        global CURR_PLAYER, NUM_PLAYERS, players

        players[CURR_PLAYER].firing = False

        CURR_PLAYER += 1
        if CURR_PLAYER >= NUM_PLAYERS.value:
            CURR_PLAYER = 0

        while not players[CURR_PLAYER].alive:
            CURR_PLAYER += 1
            if CURR_PLAYER >= NUM_PLAYERS.value:
                CURR_PLAYER = 0

    def player_explode(self, index, bullet):
        global REMAINING_PLAYERS, CURR_PLAYER, PLAYER_SCORES

        #REMAINING_PLAYERS -= 1

        if bullet.timed_out:
            if index == bullet.owner:
                PLAYER_SCORES[index] -= 1
            else:
                PLAYER_SCORES[bullet.owner] += 1
        else:
            if index == bullet.owner:
                PLAYER_SCORES[index] -= 1
            else:
                PLAYER_SCORES[bullet.owner] += 1
            self.next_turn()

    def bullet_timeout(self):
        pass

game = game_controller()

def main():
    global screen_width, screen_height, d_time, world_speed, pixels_per_meter, PLAYER_SCORES, CURR_PLAYER, camera, REMAINING_PLAYERS, game, NUM_PLAYERS, GENERATE_OUTSIDE, players, myfont, text_size, pass_by_reference_list, BULLET_TIMEOUT, MIN_PLANETS, MAX_PLANETS, bullets, planets, powerups, NUM_POWERUPS

    game_lost = False

    pygame.init()
    clock = pygame.time.Clock()

    pygame.display.set_caption("Sling shot")

    icon = pygame.Surface((100,100))
    icon.fill((255, 255, 255))
    pygame.display.set_icon(icon)

    screenf = pygame.display.set_mode([screen_width, screen_height])
    screens = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
    screen_bullet_trail = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
    screen_bullet_trail2 = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
    screen_planets = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)

    #screen_bullet_trail.blit(pygame.transform.scale(pygame.image.load('space_bg1.jpg'), (screen_width*3, screen_height*3)), (screen_width*-1, screen_height*-1))

    SPACE_DIR = 'space_bg1.jpg'
    #SPACE_DIR = 'explode.jpg'
    space_bg_zoomin = pygame.transform.scale(pygame.image.load(SPACE_DIR), (screen_width*3, screen_height*3))
    space_bg_zoomout = pygame.transform.scale(pygame.image.load(SPACE_DIR), (screen_width, screen_height))
    player_image = pygame.image.load('player.png')

    planet_images = []
    for i in range(3):
            planet_images.append(pygame.image.load('planet' + str(i) + '.png'))

    myfont = pygame.font.SysFont('arial', text_size)

    last_time = time.time_ns()

    CURR_PLAYER = 0

    space_bg_zoomin_original = space_bg_zoomin.copy()

    temp_pos = [(space_bg_zoomin.get_size()[0] - screen_width)*random.random(), (space_bg_zoomin.get_size()[1] - screen_height)*random.random()]
    temp_pos = [temp_pos[0]*-1, temp_pos[1]*-1]
    #temp_pos = [temp_pos[0]*-1, screen_height*-1]
    space_bg_zoomin_2 = pygame.transform.flip(space_bg_zoomin, True, False)

    #def __init__(self, min_pos1, max_pos1, start, speed):
    #drift_control = drift_controller((0, 0), space_bg_zoomin.get_size(), [0, 0], 0.1)

    menu_controller = menu_control(10, 15)

    #def __init__(self, textref_var, text):
    in_menu_main = menu_controller.add_element(menu_element_bool(named_value(True, "Start")))
    in_menu_settings = menu_controller.add_element(menu_control(menu_controller.element_gap, menu_controller.text_size, named_value(None, "Settings")))
    in_menu_exit = menu_controller.add_element(menu_element_bool(named_value(False, "Exit")))

    in_menu_settings.add_element(menu_element_bool(GENERATE_OUTSIDE))
    in_menu_settings.add_element(menu_element_int(NUM_PLAYERS))
    in_menu_settings.add_element(menu_element_int(MIN_PLANETS))
    in_menu_settings.add_element(menu_element_int(MAX_PLANETS))
    in_menu_settings.add_element(menu_element_int(BULLET_TIMEOUT))
    in_menu_settings.add_element(menu_element_int(NUM_POWERUPS))

    in_menu_settings.add_element(menu_element_save(named_value(None, "Save")))

    '''in_menu_settings_advanced = in_menu_settings.add_element(menu_control(menu_controller.element_gap, menu_controller.text_size, "Advanced Settings"))

    in_menu_settings_advanced.add_element(menu_element_bool(GENERATE_OUTSIDE, "Generate Outside"))
    in_menu_settings_advanced.add_element(menu_element_int(NUM_PLAYERS, "Num Players"))
    in_menu_settings_advanced.add_element(menu_element_int(MIN_PLANETS, "Min Planets"))
    in_menu_settings_advanced.add_element(menu_element_int(MAX_PLANETS, "Max Planets"))
    in_menu_settings_advanced.add_element(menu_element_int(BULLET_TIMEOUT, "Bullet Timeout"))'''

    while in_menu_main.value:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or in_menu_exit.value:
                game_run = False
                pygame.display.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    menu_controller.select_element()
                if event.key == pygame.K_DOWN:
                    menu_controller.down()
                if event.key == pygame.K_UP:
                    menu_controller.up()
                if event.key == pygame.K_ESCAPE:
                    menu_controller.exit_menu()
                if event.key == pygame.K_LEFT:
                    menu_controller.select_left()
                if event.key == pygame.K_RIGHT:
                    menu_controller.select_right()

        temp_pos[0] -= 100*d_time

        screenf.fill(0)

        if temp_pos[0] < space_bg_zoomin.get_size()[0]*-1:
            temp_pos[0] += space_bg_zoomin.get_size()[0]
            temp_surf = space_bg_zoomin.copy()
            space_bg_zoomin = space_bg_zoomin_2.copy()
            space_bg_zoomin_2 = temp_surf.copy()

        #print(temp_pos)

        screenf.blit(space_bg_zoomin, (temp_pos[0], temp_pos[1]))
        screenf.blit(space_bg_zoomin_2, (temp_pos[0] + space_bg_zoomin.get_size()[0], temp_pos[1]))

        menu_controller.draw(screenf)

        #pygame.draw.ellipse(screenf, (255, 0, 0), ((temp_pos[0] + space_bg_zoomin.get_size()[0] - 5), screen_height/2, 10, 10))
        #print((temp_pos[0] + space_bg_zoomin.get_size()[0]))

        d_time = ((time.time_ns() - last_time)/1000000000)*world_speed
        #print(1/d_time)
        last_time = time.time_ns()
        pygame.display.flip()

    '''GENERATE_OUTSIDE = pass_by_reference_list[settings_value_GENERATE_OUTSIDE]
    NUM_PLAYERS = pass_by_reference_list[settings_value_NUM_PLAYERS]
    MIN_PLANETS = pass_by_reference_list[settings_value_MIN_PLANETS]
    MAX_PLANETS = pass_by_reference_list[settings_value_MAX_PLANETS]
    BULLET_TIMEOUT = pass_by_reference_list[settings_value_BULLET_TIMEOUT]'''

    MAX_PLANETS.value = MAX_PLANETS.value - MIN_PLANETS.value
    BULLET_TIMEOUT.value = BULLET_TIMEOUT.value*1000*1000000

    space_bg_zoomin = space_bg_zoomin_original

    rand_color_list = []

    for i in range(NUM_PLAYERS.value-2):
        rand_color_list.append(randcolor_bright())

    while True:
        screenf = pygame.display.set_mode([screen_width, screen_height])
        #screens = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        screen_scores = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        screen_bullet_trail = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        screen_planets = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        screen_planets_zoomed = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)
        screen_bullet_trail2 = pygame.Surface((screen_width,screen_height), pygame.SRCALPHA)

        planets = []
        powerups = []

        #__init__(self, img, size, pos):
        #3, 2

        tempMultiplier = 1/camera_scale_zoomed

        if GENERATE_OUTSIDE.value:
            NUM_PLANETS = int(random.random()*MIN_PLANETS.value) + MAX_PLANETS.value
            for i in range(0, 3):
                #tempSize = int(random.random()*100 + 100)
                #planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))

                invalid = True
                tempSize = int(random.random()*100 + 100)
                planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))
                while invalid:
                    invalid = False
                    for p in planets:
                        if distance(planets[-1].pos, p.pos) <= p.size[0] + planets[-1].size[0] and p.pos != planets[-1].pos:
                            planets.remove(planets[-1])
                            tempSize = int(random.random()*100 + 100)
                            planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))
                            invalid = True
            for i in range(3, NUM_PLANETS):

                invalid = True
                tempSize = int(random.random()*100 + 100)
                planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width*tempMultiplier) - screen_width/2, random.random()*(screen_height*tempMultiplier) - screen_height/2]))
                while invalid:
                    invalid = False
                    for p in planets:
                        if distance(planets[-1].pos, p.pos) <= p.size[0] + planets[-1].size[0] and p.pos != planets[-1].pos:
                            planets.remove(planets[-1])
                            tempSize = int(random.random()*100 + 100)
                            planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width*tempMultiplier) - screen_width/2, random.random()*(screen_height*tempMultiplier) - screen_height/2]))
                            invalid = True

                #tempSize = int(random.random()*100 + 100)
                #planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))
                #planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width*2) - screen_width/2, random.random()*(screen_height*2) - screen_height/2]))
        else:
            NUM_PLANETS = int(random.random()*MIN_PLANETS.value) + MAX_PLANETS.value
            for i in range(NUM_PLANETS):
                #tempSize = int(random.random()*100 + 100)
                #planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))

                invalid = True
                tempSize = int(random.random()*100 + 100)
                planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))
                while invalid:
                    invalid = False
                    for p in planets:
                        if distance(planets[-1].pos, p.pos) <= p.size[0] + planets[-1].size[0] and p.pos != planets[-1].pos:
                            planets.remove(planets[-1])
                            tempSize = int(random.random()*100 + 100)
                            planets.append(planet(planet_images[int(random.random()*len(planet_images))], [tempSize, tempSize], [random.random()*(screen_width - 200) + 100, random.random()*(screen_height - 200) + 100]))
                            invalid = True

        #def __init__(self, pos, color=None, size=None):
        #powerups.append(power_up_bullet_split([screen_width/2, screen_height/2], (255, 255, 255), [10, 10]))
        print(f"{[random.random()*screen_width, random.random()*screen_height]}, {[screen_width/2, screen_height/2]}")
        for i in range(NUM_POWERUPS.value):
            invalid = True
            while invalid:
                powerups.append(power_up_bullet_split([random.random()*screen_width, random.random()*screen_height], (255, 100, 255), [10, 10]))
                #powerups.append(power_up_bullet_split([random.random()*screen_width, random.random()*screen_height], (255, 100, 255), [10, 10]))
                #print(f"\n{powerups[-1].pos}")
                invalid = False
                for p in planets:
                    if distance(powerups[-1].pos, p.pos) <= p.size[0]/2 + powerups[-1].size[0]/2:
                        #print(f"{powerups[-1].pos} to close to {p.pos}")
                        invalid = True
                        powerups.remove(powerups[-1])
                        break

        #PLAYER_SCORES = []
        players = []
        REMAINING_PLAYERS = NUM_PLAYERS.value
        #self, img, angle, power, pos
        #players.append(player(player_image, (255, 0, 0), 0, 2, [random.random()*screen_width/2, random.random()*screen_height], 0))
        #players.append(player(player_image, (0, 255, 0), 0, 2, [random.random()*screen_width/2 + screen_width/2, random.random()*screen_height], 1))
        #players.append(player(tint(player_image, (0, 255, 0)), 0, 2, [random.random()*screen_width, random.random()*screen_height]))
        #players.append(player(tint(player_image, (0, 255, 0)), 0, 2, [random.random()*screen_width, random.random()*screen_height]))

        if NUM_PLAYERS.value >= 2:
            PLAYER_SCORES.append(0)
            PLAYER_SCORES.append(0)

            invalid = True
            players.append(player(player_image, (255, 0, 0), 0, 2, [random.random()*screen_width/2, random.random()*screen_height], 0))
            while invalid:
                invalid = False
                for p in planets:
                    if distance(players[-1].pos, p.pos) <= p.size[0] + players[-1].size:
                        players.remove(players[-1])
                        players.append(player(player_image, (255, 0, 0), 0, 2, [random.random()*screen_width/2, random.random()*screen_height], 0))
                        invalid = True

            invalid = True
            players.append(player(player_image, (0, 255, 0), 0, 2, [random.random()*screen_width/2 + screen_width/2, random.random()*screen_height], 1))
            while invalid:
                invalid = False
                for p in planets:
                    if distance(players[-1].pos, p.pos) <= p.size[0] + players[-1].size:
                        players.remove(players[-1])
                        players.append(player(player_image, (0, 255, 0), 0, 2, [random.random()*screen_width/2 + screen_width/2, random.random()*screen_height], 1))
                        invalid = True
        for i in range(NUM_PLAYERS.value-2):
            PLAYER_SCORES.append(0)

            invalid = True
            players.append(player(player_image, rand_color_list[i], 0, 2, [random.random()*screen_width, random.random()*screen_height], i+2))
            while invalid:
                invalid = False
                for p in planets:
                    if distance(players[-1].pos, p.pos) <= p.size[0] + players[-1].size:
                        players.remove(players[-1])
                        players.append(player(player_image, rand_color_list[i], 0, 2, [random.random()*screen_width, random.random()*screen_height], i+2))
                        invalid = True

        bullets = []

        game_run = True

        camera.zoom_in()

        for p in planets:
            p.draw(screen_planets)

        camera.zoom_out()

        for p in planets:
            p.draw(screen_planets_zoomed)

        #normal_gravity = 9.81*pixels_per_meter

        game.next_turn()

        while game_run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_run = False
                    pygame.display.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if REMAINING_PLAYERS <= 1:
                        players[CURR_PLAYER].firing = True
                    if event.key == pygame.K_SPACE:
                        '''if not players[CURR_PLAYER].firing:
                            screen_bullet_trail = tint2(screen_bullet_trail, 35)
                            screen_bullet_trail2 = tint2(screen_bullet_trail2, 35)'''
                        players[CURR_PLAYER].shoot(bullets)
                        players[CURR_PLAYER].end_turn()
                    if event.key == pygame.K_LEFT:
                        players[CURR_PLAYER].start_left()
                    if event.key == pygame.K_RIGHT:
                        players[CURR_PLAYER].start_right()
                    if event.key == pygame.K_UP:
                        players[CURR_PLAYER].start_powup()
                    if event.key == pygame.K_DOWN:
                        players[CURR_PLAYER].start_powdown()
                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                         players[CURR_PLAYER].start_sensdown()
                    if event.key == pygame.K_TAB:
                        camera.keydown_zoom()
                    if event.key == pygame.K_a:
                        players[0].pos[0] = players[1].pos[0] + 50
                    if REMAINING_PLAYERS <= 1 and event.key == pygame.K_SPACE:
                        game_run = False
                        break
                    if event.key == pygame.K_s:
                        game_run = False
                        break
                    if len(bullets) > 0:
                        if event.key == pygame.K_d:
                            if not bullets[0].timed_out:
                                game.next_turn()
                            bullets.pop(0)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        players[CURR_PLAYER].stop_left()
                    if event.key == pygame.K_RIGHT:
                        players[CURR_PLAYER].stop_right()
                    if event.key == pygame.K_UP:
                        players[CURR_PLAYER].stop_powup()
                    if event.key == pygame.K_DOWN:
                        players[CURR_PLAYER].stop_powdown()
                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                         players[CURR_PLAYER].stop_sensdown()
                    if event.key == pygame.K_TAB:
                        camera.keyup_zoom()

            screenf.fill(0)
            screen_scores.fill(0)
            #screen_planets.fill(0)

            if camera_scale == 1:
                #screenf.blit(space_bg, (to_screen_pos2((0, 720))[0] - space_bg.get_size()[0]/2*camera_scale_zoomed, to_screen_pos2((0, 720))[1] - space_bg.get_size()[1]/2*camera_scale_zoomed))
                screenf.blit(space_bg_zoomin, (screen_width*-1, screen_height*-1))
                screenf.blit(screen_bullet_trail, (0, 0))
            else:
                screenf.blit(pygame.transform.scale(space_bg_zoomout, (screen_width, screen_height)), (0, 0))
                #screenf.blit(pygame.transform.rotozoom( screen_bullet_trail, 0, camera_scale), (camera_offset[0], camera_offset[1]))
                #screenf.blit(pygame.transform.scale(screen_bullet_trail, (int(screen_width*camera_scale), int(screen_height*camera_scale))), (camera_offset[0], camera_offset[1]))
                screenf.blit(screen_bullet_trail2, (0, 0))

            #players[CURR_PLAYER].shoot(bullets)

            camera.update(bullets)

            for i in range(len(players)):
                p = players[i]
                p.update(bullets, players)
                p.draw(screenf)
                if players[i].alive:
                    if i == CURR_PLAYER:
                        screen_scores.blit(myfont.render("PLAYER " + str(i+1) + ": " + str(int(PLAYER_SCORES[i])), True, (0, 255, 0), (50, 50, 50)), (10, 10 + text_size*i))
                    else:
                        screen_scores.blit(myfont.render("PLAYER " + str(i+1) + ": " + str(int(PLAYER_SCORES[i])), True, (255, 255, 255), (0, 0, 0)), (10, 10 + text_size*i))
                else:
                    screen_scores.blit(myfont.render("PLAYER " + str(i+1) + ": " + str(int(PLAYER_SCORES[i])), True, (255, 0, 0), (0, 0, 0)), (10, 10 + text_size*i))

            for b in bullets:
                b.update(planets, bullets)
                b.draw(screenf, screen_bullet_trail, screen_bullet_trail2)

            for p in powerups:
                p.update()
                p.draw(screenf)

            #screenf.blit(screens, (0, 0))

            if camera.scaled:
                screenf.blit(screen_planets_zoomed, (0, 0))
            else:
                screenf.blit(screen_planets, (0, 0))

            screenf.blit(screen_scores, (0, 0))

            if camera.scaled:
                screens.fill(0)
                pygame.draw.rect(screens, (0, 0, 0, 100), (camera_offset[0], camera_offset[1], screen_width*camera_scale, screen_height*camera_scale))
                screenf.blit(screens, (0, 0))

            d_time = ((time.time_ns() - last_time)/1000000000)*world_speed
            #print(1/d_time)
            last_time = time.time_ns()
            pygame.display.flip()

if __name__ == "__main__":
    main()
