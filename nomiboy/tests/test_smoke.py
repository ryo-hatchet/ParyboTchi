def test_pygame_can_init_headless():
    import pygame
    pygame.init()
    assert pygame.get_init()
    pygame.quit()
