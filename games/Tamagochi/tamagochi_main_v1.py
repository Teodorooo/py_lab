import pygame
from sys import exit
import random

class Pet(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.pet_stand = pygame.image.load('sprites/pets/pet_stand.png').convert_alpha()
		self.pet_filthy = pygame.image.load('sprites/pets/pet_filthy.png').convert_alpha()
		self.pet_bored = pygame.image.load('sprites/pets/pet_bored.png').convert_alpha()
		self.pet_hungry = pygame.image.load('sprites/pets/pet_hungry.png').convert_alpha()
		mood = [self.pet_filthy, self.pet_bored, self.pet_hungry]
		self.image = random.choice(mood)
		self.rect = self.image.get_rect(center = (400,100))
		if self.image == self.pet_filthy:
			stats['excitement'] = random.randint(5, 7)
			stats['hunger'] = random.randint(5, 7)
			stats['filth'] = random.randint(2, 4)
		elif self.image == self.pet_bored:
			stats['filth'] = random.randint(5, 7)
			stats['hunger'] = random.randint(5, 7)
			stats['excitement'] = random.randint(2, 4)
		else:
			stats['filth'] = random.randint(5, 7)
			stats['excitement'] = random.randint(5, 7)
			stats['hunger'] = random.randint(2, 4)	
	def set_sprite(self):	
		if stats['hunger'] <= 4: self.image = self.pet_hungry
		elif stats['excitement'] <= 4: self.image = self.pet_bored
		elif stats['filth'] <= 4: self.image = self.pet_filthy
		else: self.image = self.pet_stand

	def update(self):
		self.set_sprite()

def management():
	global game_active
	if stats['hunger'] > 10: stats['hunger'] = 10
	elif stats['filth'] > 10: stats['filth'] = 10
	elif stats['excitement'] > 10: stats['excitement'] = 10
	elif stats['hunger'] == 10 and stats['filth'] == 10 and stats['excitement'] == 10: game_active = 'won'
	elif stats['hunger'] <= 0 or stats['filth'] <= 0 or stats['excitement'] <= 0: game_active = 'lost'

def clock_tick():
	stats['hunger'] -= random.randint(0,3)
	stats['excitement'] -= random.randint(0,3)
	stats['filth'] -= random.randint(0,3)

class Objects(pygame.sprite.Sprite):
	def __init__(self, image, position, stat):
		super().__init__()
		self.image = image
		self.position = position
		self.rect = image.get_rect(center=position)
		self.stat = stat
	
	def get_stat(stat):
		return str(stats[stat])

	def action(self):
		if self.rect.collidepoint(pos):
			self.image.set_alpha(100)
			if event and event.type == pygame.MOUSEBUTTONUP:
				stats[self.stat] += random.randint(0,10)
				clock_tick()
		else:
			self.image.set_alpha(255)	

	def update(self):
		self.action()

pygame.init()
screen = pygame.display.set_mode((800,400))
pygame.display.set_caption('Tamagochi game')
game_active = 'start screen'
little_font = pygame.font.Font('font/Pixeltype.ttf', 40)
font = pygame.font.Font('font/Pixeltype.ttf', 50)
stats = {
    'hunger': 5,
    'filth': 5,
    'excitement': 5
}
Pet()
apple = Objects(pygame.image.load('sprites/objects/apple.png').convert_alpha(), (100,100), 'hunger')
brush = Objects(pygame.image.load('sprites/objects/brush.png').convert_alpha(), (100, 300), 'filth')
ball = Objects(pygame.image.load('sprites/objects/ball.png').convert_alpha(), (700,100), 'excitement')
pet = pygame.sprite.GroupSingle()
pet.add(Pet())
group = pygame.sprite.Group()
group.add(apple, brush, ball)

text1 = font.render('Click to start', False, 'Dark Red')
text1_rect = text1.get_rect(center=(400,200))

while True:
	event = None
	for e in pygame.event.get():
		if e.type == pygame.QUIT:
			pygame.quit()
			exit()
		event = e
	
	text3= little_font.render('Stats: hunger -> ' + Objects.get_stat('hunger') + ', filth -> ' + Objects.get_stat('filth') + ', excitement -> ' + Objects.get_stat('excitement'), False, 'Black')
	text3_rect = text3.get_rect(topleft=(150,300))

	pos = pygame.mouse.get_pos()

	screen.fill("Gray")

	if game_active == 'active':
		pet.update()
		pet.draw(screen)
		group.update()
		group.draw(screen)
		screen.blit(text3,text3_rect)
		management()
	elif game_active == 'won':
		text2 = font.render("You won!",False,'Dark Green')
		text2_rect = text2.get_rect(center=(400,100))
		screen.blit(text2,text2_rect)
	elif game_active == 'lost':
		text2 = font.render("You lost...",False,'Dark Red')
		text2_rect = text2.get_rect(center=(400,100))
		screen.blit(text2,text2_rect)
	else:
		screen.blit(text1,text1_rect)
		if e.type == pygame.MOUSEBUTTONDOWN:
			game_active = "active"

	pygame.display.flip()