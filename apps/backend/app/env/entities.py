class Structure:
    def __init__(self, built_by: str):
        self.built_by = built_by

    def __repr__(self):
        return f"Structure(built_by={self.built_by})"