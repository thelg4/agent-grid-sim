from app.env.grid import Grid


def scan_for_empty_cells(grid: Grid, limit: int = 1) -> list[tuple[int, int]]:
    """
    Scans the grid and returns up to `limit` empty cell coordinates.
    """
    results = []
    for x in range(grid.width):
        for y in range(grid.height):
            if grid.is_empty(x, y):
                results.append((x, y))
                if len(results) >= limit:
                    return results
    return results
