import pygame
import math
import sys

pygame.init()

# --- Setup ---
screen = pygame.display.set_mode((500, 500))
pygame.display.set_caption("Kreisbewegung mit Controller")
clock = pygame.time.Clock()

# --- Controller Setup ---
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("⚠️ Kein Controller gefunden!")
    pygame.quit()
    sys.exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"🎮 Controller verbunden: {joystick.get_name()}")

# --- Parameter ---
radius = 12.5
scale = 15  # Skalierung für die Anzeige (1 Einheit = 15 Pixel)
speed = 0.5
x_pos, y_pos = 0, 0  # Startposition

# --- Hauptloop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Joystick Achsen lesen ---
    axis_x = joystick.get_axis(0)  # linke Stick X-Achse
    axis_y = joystick.get_axis(1)  # linke Stick Y-Achse

    # Optional: Deadzone (damit kleine Abweichungen ignoriert werden)
    if abs(axis_x) < 0.1:
        axis_x = 0
    if abs(axis_y) < 0.1:
        axis_y = 0

    # --- Bewegung berechnen ---
    x_pos += axis_x * speed
    y_pos += axis_y * speed

    # --- Kreisbegrenzung ---
    distance = math.sqrt(x_pos**2 + y_pos**2)
    if distance > radius:
        # Skaliere Position auf den Kreisrand
        x_pos = x_pos / distance * radius
        y_pos = y_pos / distance * radius

    print(x_pos, y_pos)

    # --- Zeichnen ---
    screen.fill((20, 20, 20))

    # Kreis (Bewegungsgrenze)
    pygame.draw.circle(screen, (100, 100, 255), (250, 250), int(radius * scale), 2)

    # Punkt (aktuelle Position)
    pygame.draw.circle(
        screen,
        (255, 0, 0),
        (250 + int(x_pos * scale), 250 + int(y_pos * scale)),
        8
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()