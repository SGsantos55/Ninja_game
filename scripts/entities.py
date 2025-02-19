import pygame
import math
import random
from scripts.particle import Particle
from scripts.spark import Spark

GRAVITY = 0.4
TERMINAL_VELOCITY = 12

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size): # pass the entire game into this to give access to the entire game
        self.game = game
        self.type = e_type
        self.pos = list(pos) # ensures position is always a unique class parameter rather than a reference to a list
        self.size = size    # this is used to create the bounding rectangle (these dimensions are relative to anim_offset, which is the origin point)
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.last_movement = [0,0]

        # Animation properties
        self.action = ''
        self.anim_offset = (-3, -3) # This is the origin of the object relative to the 0,0 point on the actual sprite image
        self.flip = False
        self.set_action('idle')

    def rect(self): # this function returns the entity rectangle
        return pygame.Rect(self.pos[0],self.pos[1],self.size[0], self.size[1])

    # Function for controlling the animation state
    def set_action(self, action):
        if action != self.action: # check if animation action has changed
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy() # grab the new animation

    def update(self, tilemap, movement = (0,0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        # Apply acceleration due to gravity
        self.velocity[1] = min(TERMINAL_VELOCITY, self.velocity[1]+GRAVITY) # include a cap for terminal velocity
        
        # Determine total movement for this frame
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        # ====== Collision detection ========= # 

        # Attempt to move the entity along the x-axis
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
    
        # Check for collisions with tilemap physics objects 
        for rect in tilemap.physics_rects_around(self.pos): # loop across neighboring tiles only

            # resolve collisions in the x-axis
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        # Attempt to move the entity along the y-axis
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect() # get a copy of the entitiy's rectangle
        
        # Check for collisions with tilemap physics objects 
        for rect in tilemap.physics_rects_around(self.pos): # loop across neighboring tiles only
        
        # Resolve collisions in the y-axis
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0: 
            self.flip = True

        self.last_movement = movement # Store the last movement input

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0 # set y-velocity = 0 after collision occurs
        if self.collisions['left'] or self.collisions['right']:
            self.velocity[0] = 0 # set x-velocity = 0 after collision occurs

        self.animation.update()

    def render(self,surf,offset):
        surf.blit(pygame.transform.flip(self.animation.img(),self.flip,False),\
                  (self.pos[0]-offset[0]+self.anim_offset[0],self.pos[1]-offset[1]+self.anim_offset[1]))

# Enemy class
class Enemy(PhysicsEntity):
    def __init__(self,game,pos,size):
        super().__init__(game,'enemy',pos,size)

        self.walking = 0
        self.flip = False

    def update(self, tilemap, movement = (0,0)):
        
        # walking logic
        if self.walking:
            my_rect = self.rect() # get this entity's rectangle
            can_walk = False # initilize as false
            
            # DaFluffyPotato Logic: More efficient but not as robust (uses hard-coded values)
            # this can be improved by using anim_offset and size parameters
            # Check for a solid tile 7 pixels in front and 23 pixels below the enemy's origin point
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.rect().centery + 23)):
                can_walk = True

            # My Logic: Less efficient but robust to any entity size
            # check if there is still ground underneath and infront of us
            # for rect in tilemap.physics_rects_around(self.pos): # loop across neighboring tiles 
            #     if rect.top >= my_rect.bottom: # if the rect is below us
            #         if (not self.flip and rect.right > my_rect.right) or (self.flip and rect.left < my_rect.left): # and if the rect is in front of us
            #             can_walk = True # then we are allowed to continue walking

            # Turn around if we have collided with a wall or if we are not allowed to continue walking (about to walk off an edge)
            if self.collisions['left'] or self.collisions['right']:
                self.flip = not self.flip
            elif not can_walk:
                self.flip = not self.flip

            # Apply movement
            movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1]) # move depending on the direction the enemy is facing
            self.walking = max(0,self.walking-1) # subtract from the walking timer

            # Shoot a projectile when the walking timer runs out
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if abs(dis[1] < 16): # if the player is within +/- 1 tile in y
                    if (self.flip and dis[0] < 0): # if the player is to the left of the enemy and the enemy is facing left
                        # Spawn a projectile (left velocity)
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery],-5,0])
                        # Spawn sparks at the end of the gun barrel
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random() ))
                        # Play the shooting sound
                        self.game.sfx['shoot'].play()
                    elif (not self.flip and dis[0] > 0):
                        # Spawn a projectile (right velocity)
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery],5,0])
                        # Spawn sparks at the end of the gun barrel
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 - random.random() ))
                        # Play the shooting sound
                        self.game.sfx['shoot'].play()
        
        # for each frame that we are not walking, have a random chance to start walking again
        elif random.random() < 0.01:
            self.walking = random.randint(30,120) # this is the number of frames we will continue to walk for

        # Handle animations
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
    
        # Get nominal physics update logic
        super().update(tilemap, movement = movement)

        # Handle Enemy death (collisions with player dash attack)
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                # Generate particles
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center,angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, \
                                            velocity=[math.cos(angle+math.pi) * speed * 0.5, \
                                                        math.sin(angle+math.pi) * speed * 0.5],\
                                            frame = random.randint(0,7)))
                    self.game.sparks.append(Spark(self.rect().center, 0,       5+random.random()))
                    self.game.sparks.append(Spark(self.rect().center, math.pi, 5+random.random()))
                # Apply screenshake
                self.game.screenshake = max(25,self.game.screenshake)
                # Play death sound
                self.game.sfx['hit'].play()
                return True
            else:
                return False
        else:
            return False

    def render(self, surf, offset = (0,0)):
        super().render(surf, offset=offset)

        # Render a gun on top of the enemy
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'],True,False),\
                      (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'],(self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))
            

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 2
        self.wall_slide = False
        self.dashing = False

    def render(self, surf, offset = (0,0)):
        if abs(self.dashing) <= 50:
            super().render(surf,offset)

    def update(self, tilemap, movement=(0,0)):
        super().update(tilemap, movement=movement)

        # Handle logic for death by falling off the map
        if self.air_time > 120:
            self.game.dead += 1
            # Play death sound
            self.game.sfx['hit'].play()
            # Apply screen shake
            self.game.screenshake = max(25,self.game.screenshake)
            # Spawn a mess of particles
            for i in range(30):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(self.rect().center,angle, 2 + random.random()))
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, \
                                        velocity=[math.cos(angle+math.pi) * speed * 0.5, \
                                                    math.sin(angle+math.pi) * speed * 0.5], frame = random.randint(0,7)))

        # Logic for restoring your jump / keeping track of air time
        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 2 # reset your double jump when you hit the ground
        # take away your first jump once you've been in the air for a few frames
        if self.air_time > 4 and self.jumps == 2:
            self.jumps -=1

        # Wall Sliding Logic
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.air_time = 5
            self.velocity[1] = min(self.velocity[1],0.5) # Saturate the downwards velocity when in a wall-slide state
            
            # Show the correct animation based on which side the wall is relative to the player
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide') # set the animation state

        # Handle Running / Idling / Jumping Animations
        if not self.wall_slide:
            if self.air_time > 1: 
                self.set_action('jump')
            elif movement[0] != 0 and not (self.collisions['left'] or self.collisions['right']):
                self.set_action('run')
            else:
                self.set_action('idle')


        # Dashing logic
        # Generate a burst of particles for the dash at self.dashing == 60 and 50 (start/end of dash)
        if abs(self.dashing) in {60,50}:
            for i in range(20): # repeat 20 times
                angle = random.random() * math.pi * 2 # 0 to 2pi
                speed = random.random() * 0.5 + 0.5 # 0.5 to 1
                particle_vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                # Spawn the particle
                self.game.particles.append(Particle(self.game,'particle',self.rect().center,velocity=particle_vel,frame=random.randint(0,7))) 
        
        # Handle Dashing Movement
        if self.dashing > 0:
            self.dashing = max(0,self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0,self.dashing + 1)
        if abs(self.dashing) > 50:
            # for first 10 frames of a dash, do this
            self.velocity[0] = abs(self.dashing) / self.dashing * 10
            if abs(self.dashing) == 51:
                   self.velocity[0] *= 0.1 # take away 90% of dash velocity after 9 frames (let air drag remove the remaining velocity)
            # Generate a stream of particles for the duration of the dash
            particle_vel = [abs(self.dashing)/self.dashing * random.random()*3, 0]
            self.game.particles.append(Particle(self.game,'particle',self.rect().center,velocity=particle_vel,frame=random.randint(0,7))) 
        # The remaining 50 frames are for the dash cooldown! (can't dash until self.dashing == 0)


        # Add air drag to reduce x-velocity from wall jumps
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.5, 0) # upper bound at 0
        elif self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + 0.5, 0) # lower bound at 0


    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 6 # push away from the wall
                self.velocity[1] = -6 # jump vertically
                self.air_time = 5
                self.jumps = max(0,self.jumps-1) # lower bound number of jumps at 0
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -6 # push away from the wall
                self.velocity[1] = -6 # jump vertically
                self.air_time = 5
                self.jumps = max(0,self.jumps-1) # lower bound number of jumps at 0
                return True
        # normal jumping
        elif self.jumps: 
            self.velocity[1] = -8
            self.jumps -= 1 # take away one of the player's available jumps
            self.air_time = 5 # this forces the player to enter the jumping animation
            return True
        
        # Returns true when a jump is completed in order to have certain events activate on jumping (if you so desire)

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
