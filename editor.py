import sys
import pygame
from scripts.utils import load_images
from scripts.tilemap import Tilemap
# import json

RENDER_SCALE = 2.0

class Editor:
    def __init__(self):

        pygame.init()

        
        pygame.display.set_caption('level editor')
        self.screen = pygame.display.set_mode((640,480)) # This is what is shown on the computer screen

        self.display = pygame.Surface((320,240)) # This is the game graphics display

        self.clock = pygame.time.Clock()

        # Create a Dictionary containing all the game assets
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners')
        }

        self.movement = [False,False,False,False]

        self.tilemap = Tilemap(self, 16)
        
        # Load map.json if it exists
        try:  
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass

        self.scroll = [0,0] # create a list representing the camera position


        # Tile creation variables
        self.tile_list = list(self.assets) # calling list() with a dictionary returns a list of the keys
        self.tile_group = 0 # which category of tile are we using
        self.tile_variant = 0  # which member of the tile category are we using

        self.ongrid = True

        # Mouse input variables
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.can_place_offgrid = True

    def run(self): # This is the game loop
        while True:

            self.display.fill((0,0,0,))

            render_scroll = (int(self.scroll[0]),int(self.scroll[1])) # integer version of scroll position

            self.tilemap.render(self.display, offset = render_scroll) # render tilemap objects

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100) # make this image semi-transparent

            # Get current mouse position
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            # Place tiles
            if self.clicking:
                if not self.ongrid and self.can_place_offgrid:
                    # Add an item to the list of offgrid tiles
                    self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group],'variant': self.tile_variant, \
                                                       'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    self.can_place_offgrid = False
                elif self.ongrid:
                    # Add an item to the dictionary based on mouse position and current tile selection
                    self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], \
                                                                                        'variant': self.tile_variant, 'pos': tile_pos}
                    # print(self.tilemap.tilemap)
            # Remove tiles
            if self.right_clicking:
                # Get a key representation of the current mouse position in tile coordinates
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                # If there is a tile at the current mouse location, delete it from the dictionary
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]

                # Handle removal of offgrid tiles
                for tile in self.tilemap.offgrid_tiles.copy():
                    # for each tile in the list of offgrid tiles, get the tile's image
                    tile_img = self.assets[tile['type']][tile['variant']]
                    # Get a rectangle bounding the image of the currently selected tile
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0],tile['pos'][1] - self.scroll[1],\
                                         tile_img.get_width(),tile_img.get_height())
                    # check if the tile is colliding with the mouse
                    if tile_r.collidepoint(mpos):
                        # remove the current tile from the list of tiles
                        self.tilemap.offgrid_tiles.remove(tile)
            # Show the current tile selection
            self.display.blit(current_tile_img,(5,5))

            # blit the current tile selection near the mouse; 
            
            # if we are on-grid, the location is the tile location relative to the camera position
            if self.ongrid:
                self.display.blit(current_tile_img,(tile_pos[0]*self.tilemap.tile_size - self.scroll[0],\
                                                    tile_pos[1]*self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img,mpos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Handle Mouse Input
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True # Left Mouse Clicked
                    if event.button == 3:
                        self.right_clicking = True # Right Mouse Clicked
                    
                    # Mouse Wheel Scrolling
                    # Increment the tile group if holding shift, otherwise increment the tile variant
                    if self.shift:
                        if event.button == 4: # Mouse wheel up
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list) 
                            self.tile_variant = 0
                        elif event.button == 5: # Mouse wheel down
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list) 
                            self.tile_variant = 0
                    else:
                        if event.button == 4: # Mouse wheel up
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]]) 
                        elif event.button == 5: # Mouse wheel down
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]]) 
                        

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False # Left Mouse Released

                        # Reset ability to place offgrid tiles
                        if not self.can_place_offgrid: self.can_place_offgrid = True
                    if event.button == 3:
                        self.right_clicking = False # Right Mouse Released

                # Handle Keyboard Input

                # Camera Movement: This input detection logic is similar to axis() in unity
                if event.type == pygame.KEYDOWN:

                    # Horizontal Scrolling
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    # Vertical Scrolling
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True

                    # Shift
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        self.shift = True 
                    # Toggle on/off grid
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid 
                    # File I/O
                    if event.key == pygame.K_o: # output
                        self.tilemap.save('map.json')
                    # Auto-tiling
                    if event.key == pygame.K_t: 
                        self.tilemap.autotile()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    # Vertical Scrolling
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False

                    # Shift
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        self.shift = False 


            # Move the screen based on user input
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 3
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 3

            # self.screen.blit(self.img,self.img_pos)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()),(0,0)) # Render the game graphics onto an up-scaled display
            pygame.display.update()
            self.clock.tick(60)

Editor().run()