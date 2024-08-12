import pygame
from sys import exit
from random import randint
import json
import time
from os import remove

class Pet(pygame.sprite.Sprite):
    def __init__(self, image, position, text):
        super().__init__()
        self.initialize_pet(image, position, text) 

    def initialize_pet(self, image, position, text):
        global sprite_list, selected, pet_type, data_from_file, selection_time, scores, high_score_flag, p_amount, intervall
        selected = None
        selection_time = None
        try:
            with open('data.json', 'r') as file:
                pet_type = None
                data_from_file = json.load(file)
                selected = pygame.image.load(data_from_file["image_path"])
                stats['bored'] = data_from_file["stats"]["bored"]
                stats['hungry'] = data_from_file["stats"]["hungry"]
                stats['filthy'] = data_from_file["stats"]["filthy"]
                selection_time = data_from_file.get("selection_time")
                p_amount = data_from_file["p_amount"]
                high_score_flag = True
                current_time = time.time()
                off_time = current_time - data_from_file.get("current_time_stamp")
                off_time_flag = 0     
                while off_time_flag < int(off_time/intervall):
                    off_time_flag += 1
                    p_amount += 1
                    for stat in stats:
                        num = randint(1, 3)
                        if num == 1:
                            stats[stat] -= randint(5, 15)
        except FileNotFoundError:
            data_from_file = {"time_stamp": 0, "selection_time": None}
            n = randint(1, 3)
            if n == 1:
                stats['bored'] = randint(60, 100)
                stats['hungry'] = randint(60, 100)
                stats['filthy'] = randint(15, 25)
            elif n == 2:
                stats['filthy'] = randint(60, 100)
                stats['hungry'] = randint(60, 100)
                stats['bored'] = randint(15, 25)
            else:
                stats['filthy'] = randint(60, 100)
                stats['bored'] = randint(60, 100)
                stats['hungry'] = randint(15, 25)
            self.image = image
            self.position = position
            self.rect = self.image.get_rect(center=self.position)
            self.text_str = text
            self.text = font.render(text, False, "Light Gray")
            self.text_rect = self.text.get_rect(center=(400, 350))
            sprite_list = {"image": [], "rect": [], "text": [], "text_rect": [], "text_str": []}
            pet_type = True
            p_amount = 2

    def reset(self, image, position, text):
        self.initialize_pet(image, position, text)

    def append(self):
        sprite_list['image'].append(self.image)
        sprite_list['rect'].append(self.rect)
        sprite_list['text'].append(self.text)
        sprite_list['text_rect'].append(self.text_rect)
        sprite_list['text_str'].append(self.text_str)

    def select(self):
        if game == "active":
            choose = font.render(" Choose one of these plant pets! ", False, "Dark Green")
            choose_rect = choose.get_rect(center=(400, 50))
            global selected, sprite_list, pet_type, selection_time
            if not selected:
                self.append()
                for images, rectangles, texts, text_rects, text_strs in zip(sprite_list['image'], sprite_list['rect'], sprite_list['text'], sprite_list['text_rect'], sprite_list['text_str']):
                    images, rectangles = scaling(images, rectangles, 6.5)
                    screen.blit(images, rectangles)
                    pygame.draw.rect(screen, "Light Gray", choose_rect)
                    screen.blit(choose, choose_rect)
                    detected = animate(images, rectangles)
                    if detected["collision"]:
                        screen.blit(texts, text_rects)
                    if detected["click"]:
                        selected = images
                        pet_type = text_strs
                        selection_time = time.time()

    def update(self):
        self.select()

def place():
    global selected, pet_type
    if selected:
        selected_rect = selected.get_rect(center=(300, 225))
        if pet_type == None:
            selected, selected_rect = scaling(selected, selected_rect, 6.5)
            pet_type = False
        screen.blit(selected, selected_rect)

class Objects(pygame.sprite.Sprite):
    def __init__(self, image, position, stat):
        super().__init__()
        self.image = image
        self.position = position
        self.rect = self.image.get_rect(center=self.position)
        self.image, self.rect = scaling(self.image, self.rect, 0.555)
        self.stat = stat
        global true_objects, flag, open_flag
        flag = False
        open_flag = False
        true_objects = {"position": [], "rect": [], "image": [], "stat": []}
        self.append()
        move("out")

    def append(self):
        global true_objects
        if len(true_objects['stat']) <= 2:
            if isinstance(self.stat, str):
                true_objects['image'].append(self.image)
                true_objects['stat'].append(self.stat)
                true_objects['rect'].append(self.rect)

    def action(self):
        global open_flag
        if self.rect.collidepoint(pos):
            if event and event.type == pygame.MOUSEBUTTONDOWN:
                if not self.stat:
                    open_flag = True
                    self.stat = True
                    move("in")
                elif self.stat == True:
                    open_flag = False
                    self.stat = False
                    move("out")

    def management(self):
        global game
        if isinstance(self.stat, str):
            if stats[self.stat] > 100:
                stats[self.stat] = 100
            elif stats[self.stat] <= 0:
                game = "lost"

    def update(self):
        self.append()
        self.action()
        self.management()

def stat_incr():
    global p_amount
    if p_amount > 0:
        for rects, images, stat_keys in zip(true_objects['rect'], true_objects['image'], true_objects["stat"]):
            detected = animate(images, rects)
            if detected['click']:
                stats[stat_keys] += randint(5,15)
                p_amount -= 1
    else:
        for image in true_objects['image']:
            image.set_alpha(200)


def scaling(image, rectangle, scale):
    scaled_image = pygame.transform.scale(image, (int(image.get_size()[0] * scale), int(image.get_size()[1] * scale)))
    scaled_rectangle = scaled_image.get_rect(center=rectangle.center)
    return scaled_image, scaled_rectangle

def animate(image, rect, click=False, collision=False):
    detected = {"collision": collision, "click": click}
    if rect.collidepoint(pos):
        image.set_alpha(255)
        detected['collision'] = True
        if event and event.type == pygame.MOUSEBUTTONUP:
            detected['click'] = True
    else:
        image.set_alpha(200)
    return detected

def time_tick():
    global start_time, p_amount
    if current_time - start_time >= intervall:
        start_time = current_time
        p_amount += randint(1,2)
        for stat in stats:
            n = randint(1, 3)
            if n == 1:
                stats[stat] -= randint(5, 15)

def check_pet_type():
    if pet_type:
        return "sprites/pets/" + str(pet_type) + ".gif"
    else:
        return data_from_file["image_path"]
    
def convert_seconds(sec):
    s = sec%60
    min = int(sec/60)%60
    hr = int(sec/3600)
    return {"sec":s,"min":min,"hr":hr}

def move(placement):
    for rects in true_objects['rect']:
        if placement == "in":
            rects[0] += 150
        else:
            rects[0] -= 150

def low_stat():
    if stats["bored"] == stats["filthy"]: stats["filthy"] += 1
    if stats["bored"] == stats["hungry"]: stats["hungry"] += 1
    if stats["filthy"] == stats["hungry"]: stats["hungry"] += 1
    if min(stats.values()) <= 24:
        for keys, values in stats.items():
            if values == min(stats.values()):
                low_stat_text = font.render(f"I am {keys} !", False, "Dark Red")
                low_stat_rect = low_stat_text.get_rect(center=(425,125))
                screen.blit(low_stat_text,low_stat_rect)
               
pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption('Tamagochi-like game')
game = 'start screen'
font = pygame.font.Font('font/Pixeltype.ttf', 50)
clock = pygame.time.Clock()
start_time = time.time()
intervall = 7200
stats = {
    'hungry': 5,
    'filthy': 5,
    'bored': 5
    }

try:
    with open('scores.json', 'r') as file:
        scores = json.load(file)
except FileNotFoundError:
    scores = {'scores':[]}
    with open('scores.json', 'w') as file:
        json.dump(scores, file)
    
apple = Objects(pygame.image.load('sprites/objects/apple.png').convert_alpha(), [80, 70], 'hungry')
brush = Objects(pygame.image.load('sprites/objects/brush.png').convert_alpha(), [80, 160], 'filthy')
ball = Objects(pygame.image.load('sprites/objects/ball.png').convert_alpha(), [80, 240], 'bored')
chest_closed = Objects(pygame.image.load('sprites/objects/chest_closed.png').convert_alpha(), [450, 250], False)

dog = Pet(pygame.image.load('sprites/pets/dog.gif').convert_alpha(), (150, 200), "dog")
cat = Pet(pygame.image.load('sprites/pets/cat.gif').convert_alpha(), (400, 200), "cat")
parrot = Pet(pygame.image.load('sprites/pets/parrot.gif').convert_alpha(), (650, 200), "parrot")

pet_group = pygame.sprite.Group()
pet_group.add(dog, cat, parrot)
objects_group = pygame.sprite.Group()
objects_group.add(apple, brush, ball, chest_closed)

start_background = pygame.image.load('sprites/backgrounds/start_screen.png').convert_alpha()
start_background_rect = start_background.get_rect(center=(400, 200))
start_background, start_background_rect = scaling(start_background, start_background_rect, 0.5)

alive_background = pygame.image.load('sprites/backgrounds/mountain.png').convert_alpha()
alive_background_rect = alive_background.get_rect(center=(400, -250))
alive_background, alive_background_rect = scaling(alive_background, alive_background_rect, 1)

dead_background = pygame.image.load('sprites/backgrounds/sky.png').convert_alpha()
dead_background_rect = dead_background.get_rect(center=(400, 200))
dead_background, dead_background_rect = scaling(dead_background, dead_background_rect, 3)

house_background = pygame.image.load('sprites/backgrounds/house.png').convert_alpha()
house_background_rect = house_background.get_rect(topleft=(0, 0))

drunk = pygame.image.load("sprites/paint/drunk.jpg").convert_alpha()
drunk_rect = drunk.get_rect(center=(400, 200))
drunk, drunk_rect = scaling(drunk, drunk_rect, 0.2)

manaba = pygame.image.load("sprites/paint/manaba.jpg").convert_alpha()
manaba_rect = manaba.get_rect(center=(125, 200))
manaba, manaba_rect = scaling(manaba, manaba_rect, 0.2)

ufo = pygame.image.load("sprites/paint/ufo.jpg").convert_alpha()
ufo_rect = ufo.get_rect(center=(700, 200))
ufo, ufo_rect = scaling(ufo, ufo_rect, 0.15)

chest_opened = pygame.image.load("sprites/objects/chest_open.png").convert_alpha()
chest_opened_rect = chest_opened.get_rect(center=[449, 250])
chest_opened, chest_opened_rect = scaling(chest_opened, chest_opened_rect, 0.555)

action_menu = pygame.image.load("sprites/miscellanious/action_menu.png").convert_alpha()
action_menu_rect = action_menu.get_rect(center=(400, 200))

q_m = pygame.image.load('sprites/miscellanious/q_m.png').convert_alpha()
q_m_rect = q_m.get_rect(bottomright=(850,450))
q_m, q_m_rect = scaling(q_m, q_m_rect, 0.25)

restart = pygame.image.load("sprites/miscellanious/restart.png").convert_alpha()
restart_rect = restart.get_rect(center=(400, 275))

p_buck = pygame.image.load("sprites/miscellanious/bill.gif").convert_alpha()
p_buck_rect = p_buck.get_rect(center=(90, 325))

click_to_start = font.render('Click to start.', False, 'Dark Blue')
click_to_start_rect = click_to_start.get_rect(center=(450, 50))
 
surprise_txt = font.render('Feliz dia del padre !', False, 'White')
surprise_txt_rect = surprise_txt.get_rect(center=(400, 50))

pet_died = font.render('Your pet died...', False, "Dark Red")
pet_died_rect = pet_died.get_rect(midtop=(400, 10))

time_flag = True
score_flag = True
score_flag2 = 0
is_dict = False
high_score_flag = True

while True:
    event = None
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            if pet_type:
                scores['scores'].append(pet_type)
                with open('scores.json', 'w') as file:
                    json.dump(scores, file)
            pygame.quit()
            exit()
        event = e

    pos = pygame.mouse.get_pos()
    current_time = time.time()
    image_path = check_pet_type()

    data = {
        "stats": {
            "bored": stats['bored'],
            "filthy": stats["filthy"],
            "hungry": stats['hungry']
        },
        "p_amount": p_amount,
        "image_path": image_path,
        "time_stamp": current_time - start_time,
        "selection_time": selection_time,
        "current_time_stamp": current_time
    }

    with open('data.json', 'w') as file:
        json.dump(data, file)

    if time_flag and data_from_file['selection_time']:
        start_time -= data_from_file['time_stamp']
        selection_time = data_from_file['selection_time']
        time_flag = False
    if game == 'active':
        if selected:
            screen.blit(house_background, house_background_rect)
            time_tick()
            stat_incr()
            low_stat()
            if open_flag:
                screen.blit(action_menu, action_menu_rect)
                screen.blit(p_buck, p_buck_rect)      
                p_text = font.render(f'X {p_amount}', False, 'Dark Grey')
                p_text_rect = p_text.get_rect(midbottom=(50, 400))
                screen.blit(p_text,p_text_rect)
            objects_group.update()         
            objects_group.draw(screen)
            if open_flag:
                screen.blit(chest_opened, chest_opened_rect)
            if selection_time:
                elapsed_time = int(current_time - selection_time)
            else:
                elapsed_time = int(current_time - start_time)
            converted_time = convert_seconds(elapsed_time)
            if p_amount < 0:
                p_amount = 0
            time_text = font.render(f'Survived Time: {converted_time["hr"]} Hr, {converted_time["min"]} Min, {converted_time["sec"]} sec', False, 'Gold')
            time_text_rect = time_text.get_rect(topleft=(100, 10))
            times_list = []
            screen.blit(time_text, time_text_rect)
            screen.blit(q_m, q_m_rect)
            q_m_detected = animate(q_m, q_m_rect)
            if scores["scores"] == []:
                high_score = 0
            for i in scores["scores"]:
                score_flag2 += 1  
                if isinstance(i,dict):
                    is_dict = True
                if not is_dict and score_flag2 == len(scores["scores"]):
                    high_score = 0
                    high_score_flag = False

            if high_score_flag:
                for items in scores['scores']:
                    if isinstance(items, dict):
                        for times in items.values():
                            if isinstance(times, int):                     
                                times_list.append(times)
                                high_score = max(times_list)

            converted_high_score = convert_seconds(high_score)           
            high_score_text = font.render(f' Your high score is {converted_high_score["hr"]} Hr, {converted_high_score["min"]} Min, {converted_high_score["sec"]} Sec ', False, "Forest Green")
            high_score_rect = high_score_text.get_rect(center=(400,375))
            pygame.draw.rect(screen, "Beige", high_score_rect)
            screen.blit(high_score_text,high_score_rect)
            if q_m_detected["click"]:
                game = "q_m"
        else:
            screen.blit(alive_background, alive_background_rect)
        pet_group.update()
        place()
    
    elif game == 'lost':
        remove('data.json')
        screen.blit(dead_background, dead_background_rect)
        screen.blit(pet_died, pet_died_rect)
        screen.blit(restart, restart_rect)
        detected = animate(restart, restart_rect)
        if score_flag:
            if not pet_type and len(scores['scores']) >= 1:
                pet_type = scores['scores'][-1]
            score_dict = {'pet': pet_type, 'time': elapsed_time}
            scores['scores'].append(score_dict)
            with open('scores.json', 'w') as file:
                json.dump(scores, file)
            score_flag = False
        if detected["click"]:    
            score_flag = True
            game = "start screen"
            dog.reset(pygame.image.load('sprites/pets/dog.gif').convert_alpha(), (150, 200), "dog")
            cat.reset(pygame.image.load('sprites/pets/cat.gif').convert_alpha(), (400, 200), "cat")
            parrot.reset(pygame.image.load('sprites/pets/parrot.gif').convert_alpha(), (650, 200), "parrot")
            pet_group = pygame.sprite.Group()
            pet_group.add(dog, cat, parrot)

    elif game == "start screen":
        screen.blit(start_background, start_background_rect)
        screen.blit(click_to_start, click_to_start_rect)
        if event and event.type == pygame.MOUSEBUTTONUP:
            game = "active"

    else:
        screen.fill("Black")
        screen.blit(surprise_txt, surprise_txt_rect)
        screen.blit(drunk, drunk_rect)
        screen.blit(manaba, manaba_rect)
        screen.blit(ufo, ufo_rect)
        if event and event.type == pygame.MOUSEBUTTONUP:
            game = "active"

    pygame.display.flip()
    clock.tick(60)