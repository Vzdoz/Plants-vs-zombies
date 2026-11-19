import random
import sys
import pygame
pygame.init()

WIDTH, HEIGHT = 900, 600
FPS = 60

ROWS = 5
COLS = 9
CELL_SIZE = 80
MARGIN_X = 120
MARGIN_Y = 110

# Colors
LIGHT_GREEN = (118, 196, 78)
DARK_GREEN = (96, 174, 62)
HUD_BG = (52, 42, 34)
SUN_YELLOW = (255, 220, 50)
PLANT_GREEN = (46, 160, 67)
PEA_GREEN = (110, 235, 90)
ZOMBIE_GRAY = (120, 138, 125)
HP_RED = (210, 50, 50)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
BUTTON_BLUE = (70, 130, 180)
GOLD = (255, 215, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plants vs Zombies - Simple Pygame")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 22, bold=True)
large_font = pygame.font.SysFont("arial", 44, bold=True)


class Sun:
    def __init__(self, x, y, target_y=None, value=25):
        self.x = x
        self.y = y
        self.target_y = target_y if target_y is not None else y
        self.value = value
        self.radius = 18
        self.collected = False
        self.lifetime = FPS * 12  # Disappears after 12 seconds

    def update(self):
        if self.y < self.target_y:
            self.y = min(self.y + 1.5, self.target_y)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.collected = True

    def draw(self, surf):
        pygame.draw.circle(surf, SUN_YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.radius, 3)

    def clicked_on(self, pos):
        mx, my = pos
        return (mx - self.x) ** 2 + (my - self.y) ** 2 <= (self.radius + 6) ** 2


class Pea:
    def __init__(self, row, x, y):
        self.row = row
        self.x = x
        self.y = y
        self.speed = 6.5
        self.damage = 20
        self.radius = 8
        self.active = True

    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 20:
            self.active = False

    def draw(self, surf):
        pygame.draw.circle(surf, PEA_GREEN, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), self.radius, 2)


class Plant:
    def __init__(self, plant_type, row, col):
        self.plant_type = plant_type  # "sunflower" or "peashooter"
        self.row = row
        self.col = col
        self.x = MARGIN_X + col * CELL_SIZE + CELL_SIZE // 2
        self.y = MARGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
        self.hp = 100
        self.cooldown = FPS * 6 if plant_type == "sunflower" else FPS * 2
        self.timer = self.cooldown // 2

    def update(self, suns, peas, zombies):
        self.timer -= 1
        if self.plant_type == "sunflower":
            if self.timer <= 0:
                suns.append(Sun(self.x + random.randint(-12, 12), self.y - 10, self.y + 15))
                self.timer = self.cooldown
        elif self.plant_type == "peashooter":
            zombie_in_row = any(z.row == self.row and z.x > self.x for z in zombies)
            if zombie_in_row and self.timer <= 0:
                peas.append(Pea(self.row, self.x + 22, self.y - 4))
                self.timer = self.cooldown

    def draw(self, surf):
        if self.plant_type == "sunflower":
            pygame.draw.circle(surf, GOLD, (self.x, self.y), 24)
            pygame.draw.circle(surf, (101, 67, 33), (self.x, self.y), 13)
        else:
            pygame.draw.circle(surf, PLANT_GREEN, (self.x, self.y), 20)
            pygame.draw.rect(surf, PLANT_GREEN, (self.x, self.y - 10, 26, 14))

        if self.hp < 100:
            hp_width = max(0, int(40 * (self.hp / 100)))
            pygame.draw.rect(surf, BLACK, (self.x - 20, self.y - 34, 40, 6))
            pygame.draw.rect(surf, HP_RED, (self.x - 20, self.y - 34, hp_width, 6))


class Zombie:
    def __init__(self, row):
        self.row = row
        self.x = WIDTH + 20
        self.y = MARGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
        self.speed = 0.55
        self.hp = 1
        self.max_hp = 120
        self.bite_damage = 0.45  # Damage per frame while biting
        self.eating = False

    def update(self, plants):
        self.eating = False
        for plant in plants:
            if plant.row == self.row and abs(self.x - plant.x) < 28:
                self.eating = True
                plant.hp -= self.bite_damage
                break

        if not self.eating:
            self.x -= self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, ZOMBIE_GRAY, (self.x - 16, self.y - 28, 32, 52), border_radius=6)
        pygame.draw.circle(surf, ZOMBIE_GRAY, (int(self.x), int(self.y - 34)), 14)
        hp_width = max(0, int(36 * (self.hp / self.max_hp)))
        pygame.draw.rect(surf, BLACK, (self.x - 18, self.y - 56, 36, 6))
        pygame.draw.rect(surf, HP_RED, (self.x - 18, self.y - 56, hp_width, 6))


def get_cell(pos):
    mx, my = pos
    if (
        MARGIN_X <= mx < MARGIN_X + COLS * CELL_SIZE
        and MARGIN_Y <= my < MARGIN_Y + ROWS * CELL_SIZE
    ):
        col = (mx - MARGIN_X) // CELL_SIZE
        row = (my - MARGIN_Y) // CELL_SIZE
        return int(row), int(col)
    return None


def main():
    sun_currency = 100
    selected_plant = None  # "sunflower" or "peashooter"
    costs = {"sunflower": 50, "peashooter": 100}

    plants = []
    zombies = []
    peas = []
    suns = []

    sky_sun_timer = FPS * 7
    total_wave_zombies = 15
    spawned_zombies = 0
    zombie_timer = FPS * 10

    state = "playing"  # "playing", "victory", "game_over"

    # Top buttons to choose a plant
    btn_sunflower = pygame.Rect(220, 20, 170, 60)
    btn_peashooter = pygame.Rect(410, 20, 210, 60)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and state != "playing":
                if event.key == pygame.K_r:
                    main()
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == "playing":
                pos = event.pos

                # 1. Try to collect suns
                collected_sun = False
                for sun in suns:
                    if sun.clicked_on(pos):
                        sun_currency += sun.value
                        sun.collected = True
                        collected_sun = True
                        break
                if collected_sun:
                    continue

                # 2. Select plant card
                if btn_sunflower.collidepoint(pos):
                    selected_plant = None if selected_plant == "sunflower" else "sunflower"
                    continue
                if btn_peashooter.collidepoint(pos):
                    selected_plant = None if selected_plant == "peashooter" else "peashooter"
                    continue

                # 3. Plant on the grid
                if selected_plant:
                    cell = get_cell(pos)
                    if cell:
                        row, col = cell
                        occupied = any(p.row == row and p.col == col for p in plants)
                        cost = costs[selected_plant]
                        if not occupied and sun_currency >= cost:
                            plants.append(Plant(selected_plant, row, col))
                            sun_currency -= cost
                            selected_plant = None

        if state == "playing":
            # Suns falling from the sky
            sky_sun_timer -= 1
            if sky_sun_timer <= 0:
                sx = random.randint(MARGIN_X + 20, MARGIN_X + COLS * CELL_SIZE - 20)
                sy_dest = random.randint(MARGIN_Y + 30, MARGIN_Y + ROWS * CELL_SIZE - 20)
                suns.append(Sun(sx, MARGIN_Y - 20, sy_dest))
                sky_sun_timer = FPS * 8

            # Zombie spawning
            if spawned_zombies < total_wave_zombies:
                zombie_timer -= 1
                if zombie_timer <= 0:
                    random_row = random.randint(0, ROWS - 1)
                    zombies.append(Zombie(random_row))
                    spawned_zombies += 1
                    # Spawn slightly faster as the wave progresses
                    zombie_timer = max(FPS * 2.5, FPS * (6 - spawned_zombies * 0.2))

            # Update entities
            for sun in suns:
                sun.update()
            suns = [s for s in suns if not s.collected]

            for plant in plants:
                plant.update(suns, peas, zombies)
            plants = [p for p in plants if p.hp > 0]

            for pea in peas:
                pea.update()
            peas = [p for p in peas if p.active]

            for zombie in zombies:
                zombie.update(plants)
                if zombie.x < MARGIN_X - 35:
                    state = "game_over"

            # Pea -> zombie collisions
            for pea in peas:
                if not pea.active:
                    continue
                for zombie in zombies:
                    if zombie.row == pea.row and abs(pea.x - zombie.x) < 20 and abs(pea.y - zombie.y) < 35:
                        zombie.hp -= pea.damage
                        pea.active = False
                        break

            peas = [p for p in peas if p.active]
            zombies = [z for z in zombies if z.hp > 0]

            # Victory if all wave zombies are defeated
            if spawned_zombies >= total_wave_zombies and len(zombies) == 0:
                state = "victory"

        # --- Drawing ---
        screen.fill((34, 85, 34))

        # Top HUD bar
        pygame.draw.rect(screen, HUD_BG, (0, 0, WIDTH, 95))
        pygame.draw.circle(screen, SUN_YELLOW, (45, 42), 18)
        sun_text = font.render(f"{sun_currency}", True, WHITE)
        screen.blit(sun_text, (72, 30))

        # Sunflower button
        sunflower_color = GOLD if selected_plant == "sunflower" else BUTTON_BLUE
        pygame.draw.rect(screen, sunflower_color, btn_sunflower, border_radius=8)
        screen.blit(
            font.render("Sunflower (50)", True, BLACK),
            (btn_sunflower.x + 14, btn_sunflower.y + 18),
        )

        # Peashooter button
        peashooter_color = GOLD if selected_plant == "peashooter" else BUTTON_BLUE
        pygame.draw.rect(screen, peashooter_color, btn_peashooter, border_radius=8)
        screen.blit(
            font.render("Peashooter (100)", True, BLACK),
            (btn_peashooter.x + 12, btn_peashooter.y + 18),
        )

        # Garden 
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(
                    MARGIN_X + c * CELL_SIZE,
                    MARGIN_Y + r * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                cell_color = LIGHT_GREEN if (r + c) % 2 == 0 else DARK_GREEN
                pygame.draw.rect(screen, cell_color, rect)
                pygame.draw.rect(screen, (75, 140, 48), rect, 1)

        for plant in plants:
            plant.draw(screen)

        for zombie in zombies:
            zombie.draw(screen)

        for pea in peas:
            pea.draw(screen)

        for sun in suns:
            sun.draw(screen)

        # End-of-game screens
        if state in ("victory", "game_over"):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            msg = "You Win!." if state == "victory" else "The zombies ate your brains!"
            end_text = large_font.render(msg, True, GOLD if state == "victory" else HP_RED)
            restart_text = font.render("Press [R] to play again", True, WHITE)

            screen.blit(end_text, (WIDTH // 2 - end_text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(
                restart_text,
                (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20),
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()