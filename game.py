import sys
import random
import pygame
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.utils import load_image, load_images
from scripts.tilemap import Tilemap
from scripts.clouds import Cloud, Clouds
from scripts.utils import Animation
from scripts.particle import Particle
from scripts.spark import Spark
import math
import os

class Game:
    def __init__(self):

        pygame.init()

        # set the window title        
        pygame.display.set_caption('ninja game')

        # set the screen resolution and game screen size
        SUPPORTED_RESOLUTIONS = {'960p': [(1280, 960), (320, 240)],
                                 'HD'  : [(1920,1080), (480, 270)],
                                 'QHD' : [(2560,1440), (480, 270)],
                                 'WQHD': [(3440,1440), (720, 270)],
                                 'orig': [(640, 480),  (320, 240)]
        } 
        

        # Initialize the Screen
        # RESOLUTION = 'WQHD'
        RESOLUTION = '960p'

        SCREEN_RESOLUTION = SUPPORTED_RESOLUTIONS[RESOLUTION][0]
        GRAPHICS_DISPLAY_SIZE = SUPPORTED_RESOLUTIONS[RESOLUTION][1]

        self.screen = pygame.display.set_mode(SCREEN_RESOLUTION) # This is what is shown on the computer screen
        self.display = pygame.Surface(GRAPHICS_DISPLAY_SIZE, pygame.SRCALPHA) # This is the game graphics display
        self.display_2 = pygame.Surface(GRAPHICS_DISPLAY_SIZE) # This surface is used to create the "outlines" effect

        # Create a clock object to control frame rate
        self.clock = pygame.time.Clock()

        # Create a Dictionary containing all the game assets
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'),img_dur = 6),
            'enemy/run': Animation(load_images('entities/enemy/run'),img_dur = 4),
            'player/idle': Animation(load_images('entities/player/idle'),img_dur = 6),
            'player/run': Animation(load_images('entities/player/run'),img_dur = 4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur = 20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur = 6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        # Load Sound effects into a dictionary
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        # Apply mixing (best practice is to load sfx audio files too loud then scale down volume in-game)
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.movement = [False,False]

        self.player = Player(self,(50,50),(8,15))

        self.tilemap = Tilemap(self, 16)

        # Load the starting level
        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0 # Timer for screen shake effect

    def run(self): # This is the game loop

        # Start the music
        pygame.mixer.music.load('data/music.wav') # note that .wav files are the best for pygame sounds (issues arise with other file types)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1) # play music on an endless loop
        self.sfx['ambience'].play(-1)

        while True:
            
            # Render the base background
            self.display.fill((0,0,0,0)) # fill display with transparant background
            self.display_2.blit(pygame.transform.scale(self.assets['background'],self.display.get_size()),(0,0))

            # Increment screen shake timer
            self.screenshake = max(0, self.screenshake - 1)

            # Check if all the enemies are gone
            if not len(self.enemies):
                self.transition += 1
                # Load the next level
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps'))-1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            # Restart the level if the player dies
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1) # cap at 30 to prevent level transition from occuring outside of self.dead counter
                if self.dead > 60:
                    self.load_level(self.level)

            # Move the Camera
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 2
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 2
            render_scroll = (int(self.scroll[0]),int(self.scroll[1])) # integer version of scroll position

            # Spawn Particles
            for rect in self.leaf_spawners:
                # Note: spawn rate of particles is proportional to the size of the particle emitter rectangle
                if random.random() * 49999 < rect.width * rect.height: 
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity = [-0.1, 0.3], frame = random.randint(0,20)))


            # Update and render the level / environment
            self.clouds.update() # move the clouds
            self.clouds.render(self.display_2, offset = render_scroll) # render the clouds (render on display_2 to prevent adding the outline)

            self.tilemap.render(self.display, offset = render_scroll) # render tilemap objects

            # Update and Render the enemies
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0,0))
                enemy.render(self.display, offset = render_scroll)
                if kill:
                    self.enemies.remove(enemy)


            # Update and Render the player (if they have not died)
            if not self.dead:
                self.player.update(self.tilemap, (2*(self.movement[1] - self.movement[0]),0))
                self.player.render(self.display, offset = render_scroll)

            # Update and Render Projectiles
            self.process_projectiles(offset = render_scroll)


            # Update and render sparks
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset = render_scroll)
                if kill:
                    self.sparks.remove(spark)

            # Render the "outline" effect:
            # this logic generates a surface with black "sillhouettes" everywhere we rendered graphics onto display
            display_mask = pygame.mask.from_surface(self.display) # create a mask from the display
            display_sillhouette = display_mask.to_surface(setcolor=(0,0,0,180), unsetcolor=(0,0,0,0)) # turn the mask into a surface

            for offset in [(1,0), (-1,0), (0,-1), (0,1)]:
                self.display_2.blit(display_sillhouette,offset) # render the sillhouette onto the game graphics display

            # Update and Render Particles
            for particle in self.particles.copy(): # work with a copy of the particles list because we are removing items!
                kill = particle.update() # update particle and check if it is EOL
                particle.render(self.display,offset = render_scroll) # render each particle
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3 # add some oscillations in x-axis movement

                if kill: self.particles.remove(particle) # remove EOL particles

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            # ===== Handle User Inputs ===== #
                if event.type == pygame.KEYDOWN:
                    
                    # Horizontal Movement Detection (This input detection logic is similar to axis() in unity)
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True

                    # Handle Jumping (Allows multiple jumps)
                    if (event.key == pygame.K_UP or event.key == pygame.K_w):
                        if self.player.jump():
                            self.sfx['jump'].play()

                    # Handle Dashing
                    if event.key == pygame.K_x:
                        self.player.dash()

                    # Handle exit via escape key
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False

            # Draw a circle for transitions
            if self.transition:
                # Note that this draw operation is a bit computationally expensive
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width()//2, self.display.get_height()//2), (30 - abs(self.transition))*int(self.display.get_width()/30))
                transition_surf.set_colorkey((255,255,255)) # this makes the color white transparent on this surface
                self.display.blit(transition_surf,(0,0))

            # Handle screen shake rendering
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2 )

            # Render the game graphics onto an up-scaled display
            self.display_2.blit(self.display, (0,0)) # add nominal graphics onto the game display
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()),screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

    def quit(self):
        pygame.quit()
        sys.exit()

    def process_projectiles(self,offset=(0,0)):
        # Update and Render Projectiles
            # Projectiles is a list of all the projectiles in the game.
            # Each projectile is a 3-Dimensional list with the following data:
            # [[x,y], direction, timer]
            # Based on how Python handles lists, here are some tips:
            # projectile[0][0] is the x-coordinate
            # projectile[0][1] is the y-coordinate
            # projectile[1] is the velocity
            # projectile[2] is the number of frames that projectile has existed
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img,(projectile[0][0]-img.get_width() / 2 - offset[0], \
                                  projectile[0][1] - img.get_height() / 2 - offset[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    # Spawn spark particles upon collision with a wall
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1]>0 else 0) , 2 + random.random() ))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)

                # Logic for player collision with projectile
                elif abs(self.player.dashing) < 50 and not self.dead: # if the player is not in a dash or already dead
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1 # take damage
                        self.screenshake = max(25,self.screenshake) # this prevents a larger screen shake from being overwritten by a smaller one
                        # Play death sound
                        self.sfx['hit'].play()
                        # Spawn a mess of particles
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center,angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, \
                                                   velocity=[math.cos(angle+math.pi) * speed * 0.5, \
                                                             math.sin(angle+math.pi) * speed * 0.5], frame = random.randint(0,7)))
        
    def load_level(self,map_id):
        # Load the tilemap
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        # ===== Initilize the Level ===== #

        # create clouds
        self.clouds = Clouds(self.assets['clouds'], count=8)
        
        # initialize camera position
        self.scroll = [0,0] # create a list representing the camera position

        # Game Over State
        self.dead = 0

        # Scene transition counter
        self.transition = -30

        # initilize leaf particle spawners
        self.leaf_spawners = []
        # Create rectangles representing leaf spawning areas of all the trees
        for tree in self.tilemap.extract([('large_decor',2)], keep=True):
                self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        # initilize list of particles for particle controllers
        self.particles = []
        self.sparks = []

        # initialize list of enemies
        self.enemies = []
        
        # initialize list of projectiles
        self.projectiles = []
        

        # Spawn player and enemies by looping over all spawners in the level
        for spawner in self.tilemap.extract([('spawners',0), ('spawners',1)],keep=False):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos'] # move the player to the starting position
                self.player.air_time = 0
                self.player.dashing = 0
                self.player.velocity = [0,0]
                self.player.flip = False
            else:
                # Spawn enemies
                self.enemies.append(Enemy(self,spawner['pos'],(8,15)))

Game().run()