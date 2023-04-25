import json
import os
from typing import List
import pygame
import math
import pathlib
from tkinter import Tk, filedialog

class Utilities:
    def is_over(coords, pos, size):
        return (
            coords[0] < pos[0] < coords[0]+size and
            coords[1] < pos[1] < coords[1]+size
        )

class Sockets():
    def __init__(self, sockets):
        self.up, self.right, self.down, self.left = sockets["up"], sockets["right"], sockets["down"], sockets["left"]
    
    def rotate(self):
        self.up, self.right, self.down, self.left = self.left, self.up, self.right, self.down

class Tile():
    def __init__(self, tile : object, image : pygame.image):
        self.image = image
        self.sockets = Sockets(tile["sockets"])
        self.rotation = 0
        self.coords = (0,0)
        self.scale = 1
    
    def rotate(self, n):
        self.rotation = (self.rotation+n*90)%360
        for _ in range(n):
            self.sockets.rotate()
        return self
    
    def is_over(self, pos):
        return Utilities.is_over(self.coords, pos, self.scale)

class Tileset():
    def __init__(self, file : object):
        self.tileset = json.load(open(file))
        self.directory = pathlib.Path(file).parent
    
    def get_tiles(self):
        tiles : List[Tile] = []
        for tile in self.tileset:
            for i in range(tile["angles"]):
                tiles.append(Tile(tile, pygame.image.load(pathlib.Path(self.directory, tile["image"]))).rotate(i))
        return tiles

class Cell():
    def __init__(self, coords, tiles : List[Tile]):
        self.coords = (coords[0]*CELL_SIZE, coords[1]*CELL_SIZE)
        self.superposition = tiles
    
    def get_tile(self, pos):
        for tile in self.superposition:
            if tile.is_over(pos):
                return tile
        return None
    
    def is_over(self, pos):
        return Utilities.is_over(self.coords, pos, CELL_SIZE)
    
    def determine(self, tile):
        self.superposition = [tile]
    
    def superpose(self):
        square = math.ceil(math.sqrt(len(self.superposition)))
        for i in range(len(self.superposition)):
            supercoords = (
                i%square,
                math.floor(i/square)
            )
            tile : Tile = self.superposition[i]
            tile.coords = (
                self.coords[0]+supercoords[0]*(CELL_SIZE/square),
                self.coords[1]+supercoords[1]*(CELL_SIZE/square)
            )
            tile.scale = CELL_SIZE/square
    
    def draw(self, drawsurf : pygame.surface.Surface):
        self.superpose()
        for state in self.superposition:
            image = state.image
            image = pygame.transform.rotate(image, state.rotation)
            image = pygame.transform.scale(image, (state.scale,)*2)
            drawsurf.blit(image, state.coords)

class WFC():
    def __init__(self, tileset : Tileset):
        self.grid = [[Cell((i,j), tileset.get_tiles()) for i in range(GRID_SIZE)] for j in range(GRID_SIZE)]
        self.stack : List[Cell] = []
    
    def click(self, mousepos):
        cell = self.get_cell(mousepos)
        if not cell:
            return
        tile = cell.get_tile(mousepos)
        if not tile:
            return
        cell.determine(tile)
    
    def get_cell(self, pos):
        for row in self.grid:
            for cell in row:
                if cell.is_over(pos):
                    return cell
        return None
    
    def draw(self):
        for row in self.grid:
            for cell in row:
                cell.draw(screen)

SCREEN_SIZE = 1000
GRID_SIZE = 4
CELL_SIZE = SCREEN_SIZE / GRID_SIZE

pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))

Tk().withdraw()
wfc = WFC(Tileset(filedialog.askopenfilename()))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            wfc.click(pygame.mouse.get_pos())

    wfc.draw()

    pygame.display.flip()

pygame.quit()
