import pygame

pygame.init()
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

# Create player and enemy rects
player = pygame.Rect(200, 400, 50, 50)
enemy = pygame.Rect(200, 100, 50, 50)

running = True
while running:
    screen.fill((30, 30, 30))  # Background color

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move player with keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x -= 5
    if keys[pygame.K_RIGHT]:
        player.x += 5
    if keys[pygame.K_UP]:
        player.y -= 5
    if keys[pygame.K_DOWN]:
        player.y += 5

    # Draw objects
    pygame.draw.rect(screen, (0, 255, 0), player)
    pygame.draw.rect(screen, (255, 0, 0), enemy)

    # Check collision
    if player.colliderect(enemy):
        print("Collision detected!")

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
