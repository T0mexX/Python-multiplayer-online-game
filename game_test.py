import pygame
# from sys import exit

# pygame.init()

# screen = pygame.display.set_mode((800,400))
# pygame.display.set_caption("bo")
# clock = pygame.time.Clock()

# # test_surface = pygame.Surface((100, 200))
# # test_surface.fill("Red")
# player1_surface = pygame.transform.scale(pygame.image.load("graphics/cars/car_red.png").convert_alpha(), (90, 150))
# # player2_surface = pygame.transform.scale(pygame.image.load("graphics/car2.jpg").convert_alpha(), (50, 30))
# # player2_rect =player2_surface.get_rect(center = (200, 400))

# test_font = pygame.font.Font(None, 50) #None clould be different fonts, import .ttf files
# text_surface = test_font.render("My game", False, "Green")  #False could be AA for antialiasing


# player1_surface = pygame.transform.rotozoom(player1_surface,45,1)
# player1_rect = player1_surface.get_rect(center = (80,200 ))
# pygame.draw.rect(screen, "Pink", player1_rect)


# x = 400
# y = 0

# while True:

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             exit()
#     # player2_rect.x -= 1
#     # screen.blit(test_surface, (0,0))
#     screen.blit(player1_surface, player1_rect)
#     # screen.blit(player2_surface, player2_rect)
#     # if player1_rect.colliderect(player2_rect):
#         # player2_rect.left = 800
#     # if player2_rect.collidepoint((600, 400)):
#     #     print("bo")
#     if player1_rect.collidepoint(pygame.mouse.get_pos()):
#         print("collision mouse")
#     screen.blit(text_surface, (300, 50))
#     pygame.display.update()
#     clock.tick(60) 



# #keyboard input:

# # pygame.key.get_pressed()[pygame.K_SPACE]     #contains all the buttons with bools
# # or
# # for event in pygame.event.get()
# #   if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE 

# #time:
# # pygame.time.get_ticks() #time in ms since pygame started 

# #transform:
# # pygame.transform.scale(surface, (,))
# # pygame.transform.rotozoom(surface, rotation, scale)

# #user event:
# # event = pygame.USEREVENT + 1
# # pygame.time.set_timer(event, ms interval)

# #sprite class:
# class Player(pygame.sprite.Sprite):
#     def __init__(self):
#         super().__init__()
#         # self is needed to be called from other methods
#         self.image = pygame.transform.scale(pygame.image.load("graphics/car2.jpg").convert_alpha(), (50, 30))
#         self.rect = self.image.get_rect(center = (80, 400))
#         self.variable = 0
#         self.player_index = 0.0
#         self.player_frames = [0,0]
# # place sprites  in groups and update/display all together
# # 2 types of grouups: Group and GroupSingle
#     def player_input(self):
#         # bad for delay
#         keys = pygame.key.get_pressed()
#         if keys[pygame.K_SPACE]: self.variable += 1
    
#     def update(self):
#         self.player_input()
#         self.bo()
#         self.animation_state()

#     def animation_state(self):
#         self.player_index += 0.1
#         if self.player_index >= len(self.player_frames): self.player_index = 0.0
#         self.image = self.player_frames[int(self.player_index)]
# player = pygame.sprite.GroupSingle()
# player.add(Player())
# player.draw(screen)
# player.update()

# class Obstacle(pygame.sprite.Sprite):
#     def __init__(self):
#         super().__init__()



#         # self.image = 
#         # self.rect = 

print(pygame.font.get_fonts())