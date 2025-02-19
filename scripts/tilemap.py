import pygame
import json

NEIGHBOR_OFFSETS = [(-1,0),(-1,-1),(0,-1),(1,-1),(1,0),(0,0),(1,1),(0,1),(-1,1)] # get all the tiles in these grid positions relative to the player
PHYSICS_TILES = {'grass','stone'} # this is a set; it is faster to check if a value is in a set rather than if a value is in a list
AUTOTILE_TYPES = {'grass','stone'} # which tile types can be autotiled

# Define rules for auto-tiling
AUTOTILE_MAP = {
    # Each dictionary key is a sorted list containing tile neighbors to check for, converted to a tuple
    # because dictionaries cannot have lists as keys
    # Each dictionary entry is the tile variant to use to if the neighbors in the key are populated
    tuple(sorted([(1, 0,), (0, 1)])):                   0, # tiles on the right and below 
    tuple(sorted([(1, 0,), (-1, 0), (0, 1)])):          1, # tiles on left, right, and below
    tuple(sorted([(-1, 0,), (0, 1)])):                  2, # tiles left and below
    tuple(sorted([(-1, 0,), (0, -1), (0, 1)])):         3, # tiles left, above, below
    tuple(sorted([(-1, 0,), (0, -1)])):                 4, # tiles left and above
    tuple(sorted([(-1, 0,), (1, 0), (0, -1)])):         5, # tiles left, right, and above
    tuple(sorted([(1, 0,), (0, -1)])):                  6, # tiles right and above
    tuple(sorted([(1, 0,), (0, 1), (0, -1)])):          7, # tiles above, below, and right
    tuple(sorted([(-1, 0,), (1, 0), (0, -1), (0, 1)])):  8, # tiles on left, right, above, and below
}

class Tilemap:
    def __init__(self, game, tile_size = 16): # 16 is the default tile size
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {} # this is a dictionary to map each tile to a location
        self.offgrid_tiles = [] # this is a list of all decorations to be placed off the tile grid


        # ============ Tilemap Data ===================#
        # Note: Tilemap data are dictionaries whose key is a string representing a position (tile coordinates for tilemap objects, 
        # pixels for off-grid tile objects), and whose entry is another dictionary containing image and position info for each object

        # Template for putting tiles into a dictionary
        # {(0,0): 'grass', (0,1): 'dirt', (9999, 0): 'grass'} # save individual tile locations as specific tiles 
        # (this allows you to not have to code empty spaces into a list!)

        # Generate sample tilemap data
        # for i in range(10):
        #     # results in positions 3 thru 12 on x, 10 on y being grass tiles
        #     self.tilemap[str(3+i) + ';10'] = {'type': 'grass', 'variant': 1, 'pos': (3+i,10)} # keep pos as a tuple, everything else is a string
        #     self.tilemap['10;' + str(5+i)] = {'type': 'stone', 'variant': 1, 'pos': (10,5+i)}

        # # generate decorations data (note that position refers to the top-left of each image!)
        # self.offgrid_tiles.append({'type': 'large_decor', 'variant': 2, 'pos': (100,100)}) # add a tree at (100,100) in pixel coordinates
        # self.offgrid_tiles.append({'type': 'large_decor', 'variant': 0, 'pos': (200,130)}) # add a rock at (200,130) in pixel coordinates

    def render(self,surf, offset = (0,0)):

        # Render decorations first!
        for tile in self.offgrid_tiles: # this will render all decoration items, even if they are not inside the camera view
            surf.blit(self.game.assets[tile['type']][tile['variant']],(tile['pos'][0] - offset[0],\
                tile['pos'][1] - offset[1])) # position is in pixels for off-grid graphics
    
        # identify and loop through tilemap tiles inside the camera view
        for x in range(offset[0] // self.tile_size - 1, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size - 1, (offset[1] + surf.get_height()) // self.tile_size + 1):
                tile_loc =  str(x) + ';' + str(y)
                if tile_loc in self.tilemap:
                    tile = self.tilemap[tile_loc] 
                    # render this tile if it is in the camera view 
                    surf.blit(self.game.assets[tile['type']][tile['variant']],\
                              (tile['pos'][0]*self.tile_size - offset[0], tile['pos'][1]*self.tile_size - offset[1]))

    def extract(self, id_pairs, keep = False):

        # id_pairs is a list of tuples of the form ('type',int variant) where 'type' is the type of tile

        # return tiles in id_pairs, optionally remove them from the map
        matches = [] # initialize empty list of matches w/ id pairs
        
        # Loop through off-grid tiles
        for tile in self.offgrid_tiles.copy(): # work with a copy of offgrid_tiles rather than the actual parameter
            # if the tile type and variant listed in id_pairs exists in offgrid tiles:
            if (tile['type'],tile['variant']) in id_pairs:
                matches.append(tile.copy()) # pass the tile information to matches list
                # remove from offgrid tiles if specified
                if not keep:
                    self.offgrid_tiles.remove(tile)

        # Loop through on grid tiles (by dictionary keys)
        for loc in self.tilemap.copy():
            tile = self.tilemap[loc] # tilemap is a dictionary; get the entry corresponding to [loc] (this is the actual dictionary entry, not a working copy!)
            if (tile['type'], tile['variant']) in id_pairs:

                # Create a clean copy of the tile data to avoid modifying the actual data
                # in self.tilemap
                matches.append(tile.copy()) # pass the tile information to matches list
                # create a copy of the matches list entry (list.copy function)
                matches[-1]['pos'] = matches[-1]['pos'].copy() # don't really understand why we have to copy this one
                # convert tilemap position to pixel coordinates
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size

                # remove from tilemap if specified
                if not keep:
                    del self.tilemap[loc] # remove from dictionary

        return matches
   
    def tiles_around(self,pos): # get the neighboring tiles relative to a given position in the game world
        
        tiles = [] # initialize list of tiles to return
        # converta pixel position into a grid position
        tile_loc = (int(pos[0] // self.tile_size),int(pos[1] // self.tile_size)) # double slash is integer division, which drops the decimals after division
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap: # check if there is a tile in this location ( I guess this already knows to check the 'pos' key)
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    # filter tiles that have physics enabled
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0]*self.tile_size, tile['pos'][1]*self.tile_size,self.tile_size,self.tile_size))
        return rects
    
    # function to check if a solid physics tile exists at a query point and return said tile
    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size)) # convert pos to tile coordinates
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    # Save Tilemap data
    def save(self, path): 
        f = open(path, 'w') # create file with write access
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles},f)
        f.close()

    # Load Tilemap data
    def load(self, path): 
        # Load a saved json file
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        # Parse loaded data to class parameters
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    # Auto-tiling 
    def autotile(self):
        # loop through all the keys in the tilemap dictionary
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1,0),(-1,0),(0,-1),(0,1)]:
                # build a string representation of the location we want to check
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                # Check if something exists in the checked location
                if check_loc in self.tilemap:
                    # if yes, make sure the neighbor is the same type of tile
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift) # add this location to the set of populated neighbors

            # Convert neighbors set into a tuple for compatability with the autotile rule dictionary
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                # set this tile's variant to the entry in the rule dictionary
                tile['variant'] = AUTOTILE_MAP[neighbors] 

