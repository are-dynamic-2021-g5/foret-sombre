import pygame as pg
import random

pg.init()

WIDTH, HEIGHT = 1000, 1000
WIN = pg.display.set_mode((WIDTH, HEIGHT))

BLACK = 0, 0, 0
WHITE = 255, 255, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
YELLOW = 255, 255, 0

FPS = 60

def spawn(nst, npl, nhpl):
	#random.seed(1)
	for i in range(nst):
		rd_x, rd_y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
		pg.draw.circle(WIN, WHITE, (rd_x, rd_y), 10)
		rd_npl = random.randint(0, npl)
		rd_nhpl = random.randint(0,nhpl)
		for j in range(rd_npl):
			r = 50
			pl_x, pl_y = random.randint(rd_x-r, rd_x+r), random.randint(rd_y-r, rd_y+r)
			if rd_nhpl > 0:
				pg.draw.circle(WIN, GREEN, (pl_x, pl_y), 5)
				rd_nhpl -= 1
			else:
				pg.draw.circle(WIN, RED, (pl_x, pl_y), 5)



def main():

	run = True
	clock = pg.time.Clock()
	spawn(20, 5, 2)

	while run:
		clock.tick(FPS)	
		for event in pg.event.get():
			if event.type == pg.QUIT:
				run = False

		pg.display.flip()
	pg.quit()

if __name__ == "__main__":
	main()