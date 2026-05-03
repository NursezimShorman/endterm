import pygame

def flood_fill(surface, x, y, new_color):
    width, height = surface.get_size()

    # bounds check
    if x < 0 or x >= width or y < 0 or y >= height:
        return

    target_color = surface.get_at((x, y))[:3]
    new_color = new_color[:3]

    if target_color == new_color:
        return

    stack = [(x, y)]

    while stack:
        x, y = stack.pop()

        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        current_color = surface.get_at((x, y))[:3]

        if current_color == target_color:
            surface.set_at((x, y), new_color)

            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))
