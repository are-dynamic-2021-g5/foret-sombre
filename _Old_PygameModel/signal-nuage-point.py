import pygame as pg
import random, math

pg.init()

WIDTH, HEIGHT = 500, 500
WIN = pg.display.set_mode((WIDTH, HEIGHT))

BLACK = 0, 0, 0
WHITE = 255, 255, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
YELLOW = 255, 255, 0

FPS = 20
NB_CIVS = 10
NB_STARS = 5

class Civ:
	def __init__(self, pos, classe=1, color=BLUE, signal_range=200):
		self.classe = classe
		self.pos = pos
		self.x = pos[0]
		self.y = pos[1]
		self.color = color
		self.size = 5

		#signal
		self.signal_type = 'dots'
		self.signal_accuracy = 100
		self.signal_number = self.signal_accuracy
		self.signal_size = 0
		self.signal_range = signal_range
		self.signal_speed = 1
		self.get_signal = False
		self.signal = []


		#detection
		self.detected_civs = []
		self.is_detected = False

	def draw(self):
		pg.draw.circle(WIN, self.color, self.pos, self.size)

	def init_signal(self):
		for i in range(self.signal_accuracy):
			self.signal.append((i, pg.draw.circle(WIN, WHITE, (self.x, self.y), 2)))

	def draw_signal(self):
		for i in range(len(self.signal)):
			index, _ = self.signal[i]
			signal_x = self.signal_size*math.cos(2*math.pi*index/self.signal_accuracy)+self.x
			signal_y = self.signal_size*math.sin(2*math.pi*index/self.signal_accuracy)+self.y
			self.signal[i] = (index, pg.draw.circle(WIN, WHITE, (signal_x, signal_y), 2))

	def update_signal(self):
		if self.signal_size >= self.signal_range:
			self.signal_size = 0
			self.init_signal()
		else:
			self.signal_size += 1
		self.draw_signal()

	def check_signal_collision(self, Star_list, destroy=True):
		for index, srect in self.signal:
			for j in range(len(Star_list)):
				if pg.Rect.colliderect(srect, Star_list[j].rect):
					for i in range(len(self.signal)):
						if self.signal[i][0] == index:
							self.signal.pop(i)
							break

class Star:

	def __init__(self, pos, size=20, color=YELLOW):
		self.pos = pos
		self.x = pos[0]
		self.y = pos[1]

		self.size = size
		self.color = color
		self.rect = None

		self.is_obstruing = []

	def draw(self):
		self.rect = pg.draw.circle(WIN, self.color, self.pos, self.size)

def draw_window():
	WIN.fill(BLACK)
	draw_scale(50) 

def init_civs():
	random.seed(1)
	global civs
	civs = []
	for i in range(NB_CIVS):
		rd_x, rd_y = random.randint(0, 500), random.randint(0, 500)
		civs.append(Civ((rd_x, rd_y)))

def init_stars():
	random.seed(3)
	global stars
	stars = []
	for i in range(NB_STARS):
		rd_x, rd_y = random.randint(0, 500), random.randint(0, 500)
		stars.append(Star((rd_x, rd_y)))

def draw_civs():
	font = pg.font.SysFont("arial", 15)
	for i in range(len(civs)):
		civs[i].draw()
		img = font.render(str(i), True, WHITE)
		WIN.blit(img, civs[i].pos)

def draw_stars():
	font = pg.font.SysFont("arial", 15)
	for i in range(len(stars)):
		stars[i].draw()
		img = font.render(str(i), True, BLACK)
		WIN.blit(img, stars[i].pos)

def draw_scale(scale_al):
	# 1:10 -> 1px = 10 al
	pg.draw.line(WIN, WHITE, (530, 580), (580, 580))
	font = pg.font.SysFont("arial", 15)
	img = font.render(str(scale_al), True, WHITE)
	WIN.blit(img, (558, 582))

def check_detection():
	for i in range(len(civs)):
		for c in range(len(civs)):
			if i != c:
				d = math.sqrt((civs[i].x-civs[c].x)**2 + (civs[i].y-civs[c].y)**2)
				if civs[i].signal_size >= d and not c in civs[i].detected_civs:
					civs[i].detected_civs.append(c)
					# print(i, "has detected", c)
					civs[c].is_detected = True
					civs[c].color = RED
		for s in range(len(stars)):
			d = math.sqrt((civs[i].x-stars[s].x)**2 + (civs[i].y-stars[s].y)**2)
			if civs[i].signal_size >= d:
				stars[s].is_obstruing.append(civs[i].pos)	

def draw_dotcircle(pos, acc):
	dots = []
	for i in range(acc):
		pass
	return dots
	
def main():

	clock = pg.time.Clock()
	run = True

	init_civs()
	init_stars()

	civs[5].init_signal()

	while run:
		clock.tick(FPS)	
		for event in pg.event.get():
			if event.type == pg.QUIT:
				run = False

		draw_window()
		draw_civs()
		draw_stars()

		civs[5].update_signal()

		civs[5].check_signal_collision(stars)

		pg.display.flip()
	pg.quit()

if __name__ == "__main__":
	main()