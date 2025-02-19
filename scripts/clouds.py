import random 

class Cloud:
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos) # convert to list so we can deal with tuples
        self.img = img # do not create a copy of the image, saves memory\
        self.speed = speed
        self.depth = depth

    def update(self):
        # move the cloud based on its speed
        self.pos[0] += self.speed

    def render(self, surf, offset = (0,0)):
        render_pos = (self.pos[0] - offset[0]*self.depth, self.pos[1] - offset[1]*self.depth) # depth creates a "parallax" effect
        surf.blit(self.img,(render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(), \
                            render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height())) # use the mod operator to loop the cloud across the screen

class Clouds: # class to store all the clouds in the scene
    def __init__(self, cloud_images, count = 16):
        self.clouds = []
        
        # Generate count number of clouds at random positions, chosing a random variant of the cloud image, with random speed (alawys moving right)
        # and random depth (always at least 0.2); recall that random.random produces a random float between 0.0 and 1.0
        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images), \
                                      random.random()* 0.05 + 0.05, random.random() * 0.6 + 0.2))
            
        self.clouds.sort(key = lambda x: x.depth) # sort the list of clouds based on depth (clouds at farther depth get rendered first)

    def update(self):
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset = (0,0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)