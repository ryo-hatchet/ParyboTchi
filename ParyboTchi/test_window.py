"""最小限のpygameウィンドウテスト"""
import pygame

pygame.init()
screen = pygame.display.set_mode((240, 240))
pygame.display.set_caption("ParyboTchi Test")

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 255, 255), (100, 120), 8)
    pygame.draw.circle(screen, (255, 255, 255), (140, 120), 8)

    clock.tick(30)
    pygame.display.flip()

pygame.quit()
print("正常終了")
