import math
import sys
import pygame

WIDTH, HEIGHT = 800, 600
CENTER = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
MAX_RADIUS = 200
DEADZONE = 0.12
SPEED = 5.0

pygame.init()
pygame.joystick.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Joystick Fadenkreuz")
clock = pygame.time.Clock()

if pygame.joystick.get_count() == 0:
    print("Kein Controller gefunden.")
    pygame.quit()
    sys.exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print("Controller:", joystick.get_name())

pos = pygame.Vector2(CENTER)

def apply_deadzone(value, dz):
    if abs(value) < dz:
        return 0.0
    return value

running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.JOYDEVICEREMOVED:
            running = False

    pygame.event.pump()

    x = apply_deadzone(joystick.get_axis(0), DEADZONE)
    y = apply_deadzone(joystick.get_axis(1), DEADZONE)

    move = pygame.Vector2(x, y) * SPEED * 60 * dt
    pos += move

    offset = pos - CENTER
    length = offset.length()

    if length > MAX_RADIUS:
        offset.scale_to_length(MAX_RADIUS)
        pos = CENTER + offset

    screen.fill((20, 20, 20))

    pygame.draw.circle(screen, (80, 80, 80), (int(CENTER.x), int(CENTER.y)), MAX_RADIUS, 2)
    pygame.draw.line(screen, (120, 120, 120), (int(CENTER.x - MAX_RADIUS), int(CENTER.y)),
                     (int(CENTER.x + MAX_RADIUS), int(CENTER.y)), 1)
    pygame.draw.line(screen, (120, 120, 120), (int(CENTER.x), int(CENTER.y - MAX_RADIUS)),
                     (int(CENTER.x), int(CENTER.y + MAX_RADIUS)), 1)

    cx, cy = int(pos.x), int(pos.y)
    pygame.draw.line(screen, (255, 0, 0), (cx - 15, cy), (cx + 15, cy), 2)
    pygame.draw.line(screen, (255, 0, 0), (cx, cy - 15), (cx, cy + 15), 2)
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)

    font = pygame.font.SysFont(None, 24)
    txt = font.render(f"Axis0: {x:.2f}  Axis1: {y:.2f}", True, (230, 230, 230))
    screen.blit(txt, (10, 10))

    pygame.display.flip()
