import pygame
import os

BASE_IMG_PATH = 'data/images/'

# load a specific image as a surface
def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0,0,0))
    return img

# loads all the images in a folder (returns a list of surfaces)
def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)): # os.listdir will return a list of all files in a directory
        images.append(load_image(path + '/' + img_name))
    return images

# Class for playing animations
class Animation:
    def __init__(self, images, img_dur=5, loop = True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0 # this value will be incremented every frame of the game

    # create a copy instance of this animation (saves memory, somehow..)
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    # returns current image of the animation
    def img(self):
        return self.images[int(self.frame / self.img_duration)] # gives us whatever frame we are on for the current frame of the game
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images)) # make the image loop around the number of frames in the animation
        else:
            self.frame = min(self.frame+1, self.img_duration * len(self.images) - 1) # this needs a -1 for 0 index, above doesn't due to modulus operation
            if self.frame >= self.img_duration*len(self.images) - 1:
                self.done = True