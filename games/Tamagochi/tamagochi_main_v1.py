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
		global hunger, excitement, filth
		if self.image == self.pet_filthy:
			excitement = random.randint(5,7)
			hunger = random.randint(5,7)
			filth = random.randint(2,4)
		elif self.image == self.pet_bored:
			filth = random.randint(5,7)
			hunger = random.randint(5,7)
			excitement = random.randint(2,4)
		else:
			filth = random.randint(5,7)
			excitement = random.randint(5,7)
			hunger = random.randint(2,4)
	
	def set_sprite(self):	
		if hunger <= 4: self.image = self.pet_hungry
		elif excitement <= 4: self.image = self.pet_bored
		elif filth <= 4: self.image = self.pet_filthy
		else:
			self.image = self.pet_stand

	def update(self):
		self.set_sprite()


def clock_tick():
	global hunger, filth, excitement
	hunger -= random.randint(0,1)
	excitement -= random.randint(0,1)
	filth -= random.randint(0,1)


def management():
	global hunger, filth, excitement, game_active, text2_str
	if hunger > 10: hunger = 10
	elif filth > 10: filth = 10
	elif excitement > 10: excitement = 10
	elif hunger == 10 and filth == 10 and excitement == 10: 
		game_active = 'won'
		print(game_active)
	elif hunger <= 0 or filth <= 0 or excitement <= 0: 
		game_active = 'lost'
		print(game_active)

class Ball(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.image = pygame.image.load('sprites/objects/ball.png').convert_alpha()
		self.rect = self.image.get_rect(center = (700,100))

	def play(self,event):
		global excitement
		if self.rect.collidepoint(pos):
			self.image.set_alpha(100)
			if event and event.type == pygame.MOUSEBUTTONUP:
				excitement += random.randint(6,8)
				clock_tick()	
		else:
			self.image.set_alpha(255)

	def get_excitement():
		return str(excitement)

	def update(self,event):
		self.play(event)

class Brush(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.image = pygame.image.load('sprites/objects/brush.png').convert_alpha()
		self.rect = self.image.get_rect(center = (100,300))

	def clean(self,event):
		global filth
		if self.rect.collidepoint(pos):
			self.image.set_alpha(100)
			if event and event.type == pygame.MOUSEBUTTONUP:
				filth += random.randint(6,8)
				clock_tick()
		else:
			self.image.set_alpha(255)
	
	def get_filth():
		return str(filth)

	def update(self,event):
		self.clean(event)

class Apple(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.image = pygame.image.load('sprites/objects/apple.png').convert_alpha()
		self.rect = self.image.get_rect(center = (100,100))

	def eat(self,event):
		global hunger
		if self.rect.collidepoint(pos):
			self.image.set_alpha(100)
			if event and  event.type == pygame.MOUSEBUTTONUP: 
				hunger += random.randint(6,8)
				clock_tick()
		else: 
			self.image.set_alpha(255)
	
	def get_hunger():
		return str(hunger)

	def update(self,event):
		self.eat(event)

pygame.init()
screen = pygame.display.set_mode((800,400))
pygame.display.set_caption('Tamagochi game')
game_active = 'bruh'
little_font = pygame.font.Font('font/Pixeltype.ttf', 40)
font = pygame.font.Font('font/Pixeltype.ttf', 50)

pet = pygame.sprite.GroupSingle()
pet.add(Pet())
apple = pygame.sprite.GroupSingle()
apple.add(Apple())
brush = pygame.sprite.GroupSingle()
brush.add(Brush())
ball = pygame.sprite.GroupSingle()
ball.add(Ball())

text1 = font.render('Click to start', False, 'Dark Red')
text1_rect = text1.get_rect(center=(400,200))

while True:
	event = None
	for e in pygame.event.get():
		if e.type == pygame.QUIT:
			pygame.quit()
			exit()
		event = e
	
	text3= little_font.render('Stats: hunger -> ' + Apple.get_hunger() + ', filth -> ' + Brush.get_filth() + ', excitement -> ' + Ball.get_excitement(), False, 'Black')
	text3_rect = text3.get_rect(topleft=(150,300))

	pos = pygame.mouse.get_pos()

	screen.fill("Gray")

	if game_active == 'active':
		pet.update()
		pet.draw(screen)
		apple.update(event)
		apple.draw(screen)
		brush.update(event)
		brush.draw(screen)
		ball.update(event)
		ball.draw(screen)
		screen.blit(text3,text3_rect)
		management()
	elif game_active == 'won':
		text2 = font.render("you won!",False,'Green')
		text2_rect = text2.get_rect(center=(400,100))
		screen.blit(text2,text2_rect)
	elif game_active == 'lost':
		text2 = font.render("you lost...",False,'Red')
		text2_rect = text2.get_rect(center=(400,100))
		screen.blit(text2,text2_rect)
	else:
		screen.blit(text1,text1_rect)
		if e.type == pygame.MOUSEBUTTONDOWN:
			game_active = "active"
	

		

	pygame.display.flip()