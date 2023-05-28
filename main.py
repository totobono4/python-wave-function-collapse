from tkinter import Tk, filedialog
from typing import List
from typing import Dict
import pathlib
import pygame
import json
import math
import copy

class Utilities:
    def is_over(coords, pos, size) -> bool:
        return (
            coords[0] <= pos[0] < coords[0]+size and
            coords[1] <= pos[1] < coords[1]+size
        )

    def opposites(direction) -> str:
        return {
            "up": "down",
            "right": "left",
            "down": "up",
            "left": "right"
        }[direction]

class Tile():
    def __init__(self, tile : object, image : pygame.image):
        self.image = image
        self.sockets : Dict[str, str] = copy.deepcopy(tile["sockets"])
        self.rotation = 0
        self.coords = (0,0)
        self.scale = 1
    
    def rotate(self, n) -> None:
        self.rotation = (self.rotation+n*-90)%360
        for _ in range(n):
            self.sockets["up"], self.sockets["right"], self.sockets["down"], self.sockets["left"] = self.sockets["left"], self.sockets["up"], self.sockets["right"], self.sockets["down"]
        return self
    
    def is_over(self, pos) -> bool:
        return Utilities.is_over(self.coords, pos, self.scale)

class Tileset():
    def __init__(self, file : object):
        self.tileset = json.load(open(file))
        self.directory = pathlib.Path(file).parent
    
    def get_tiles(self) -> List[Tile]:
        tiles : List[Tile] = []
        for tile in self.tileset:
            for i in range(tile["angles"]):
                tiles.append(Tile(tile, pygame.image.load(pathlib.Path(self.directory, tile["image"]))).rotate(i))
        return tiles

class Cell():
    def __init__(self, coords, tiles : List[Tile]):
        self.coords = (coords[0]*CELL_SIZE, coords[1]*CELL_SIZE)
        self.superposition : List[Tile] = tiles
    
    def get_tile(self, pos) -> Tile:
        for tile in self.superposition:
            if tile.is_over(pos):
                return tile
        return None
    
    def is_over(self, pos) -> bool:
        return Utilities.is_over(self.coords, pos, CELL_SIZE)
    
    def determine(self, tiles : List[Tile]) -> None:
        self.superposition = tiles
    
    def superpose(self) -> None:
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
    
    def draw(self, drawsurf : pygame.surface.Surface) -> None:
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
    
    def collapse(self, cell : Cell) -> None:
        if cell == None:
            return

        before_collapse = len(cell.superposition)

        self.collapse_neighbor(cell, "up")
        self.collapse_neighbor(cell, "right")
        self.collapse_neighbor(cell, "down")
        self.collapse_neighbor(cell, "left")

        after_collapse = len(cell.superposition)

        if before_collapse == after_collapse:
            return

        self.collapse(self.get_cell_neighbors(cell)["up"])
        self.collapse(self.get_cell_neighbors(cell)["right"])
        self.collapse(self.get_cell_neighbors(cell)["down"])
        self.collapse(self.get_cell_neighbors(cell)["left"])
    
    def collapse_neighbor(self, cell : Cell, direction : str):
        opposite = Utilities.opposites(direction)
        neighbors = self.get_cell_neighbors(cell)

        if neighbors[direction] != None:
            determinors : List[Tile] = neighbors[direction].superposition
            superposition : List[Tile] = []
        
            for tile in cell.superposition:
                is_matching : bool = False
                for determinor_tile in determinors:
                    if tile.sockets[direction] == determinor_tile.sockets[opposite]:
                        is_matching = True
                if is_matching:
                    superposition.append(tile)
            
            cell.determine(superposition)

    def get_cell_neighbors(self, cell : Cell) -> Dict[str, Cell]:
        return {
            "up": self.get_cell((cell.coords[0], cell.coords[1] - CELL_SIZE)),
            "right": self.get_cell((cell.coords[0] + CELL_SIZE, cell.coords[1])),
            "down": self.get_cell((cell.coords[0], cell.coords[1] + CELL_SIZE)),
            "left": self.get_cell((cell.coords[0] - CELL_SIZE, cell.coords[1]))
            }

    def click(self, mousepos) -> None:
        cell = self.get_cell(mousepos)
        if not cell:
            return
        tile = cell.get_tile(mousepos)
        if not tile:
            return
        cell.determine([tile])
        neighbors = self.get_cell_neighbors(cell)
        self.collapse(neighbors["up"])
        self.collapse(neighbors["right"])
        self.collapse(neighbors["down"])
        self.collapse(neighbors["left"])
    
    def get_cell(self, pos) -> Cell:
        for row in self.grid:
            for cell in row:
                if cell.is_over(pos):
                    return cell
        return None
    
    def draw(self) -> None:
        for row in self.grid:
            for cell in row:
                cell.draw(screen)

SCREEN_SIZE = 500
GRID_SIZE = 5
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

    screen.fill((0,0,0))
    wfc.draw()

    pygame.display.flip()

pygame.quit()
