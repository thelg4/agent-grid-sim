from app.env.grid import Grid


def move_agent_randomly(agent_id: str, grid: Grid) -> tuple[int, int] | None:
    import random

    current = grid.find_agent(agent_id)
    if not current:
        return None

    x, y = current
    random.shuffle(grid.directions)

    for dx, dy in grid.directions:
        nx, ny = x + dx, y + dy
        if grid.is_within_bounds(nx, ny) and grid.is_empty(nx, ny):
            grid.move_agent(agent_id, (nx, ny))
            return nx, ny

    return None  # No move possible
