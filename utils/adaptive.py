DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


def get_next_difficulty(current_difficulty, is_correct):
    current_index = DIFFICULTY_LEVELS.index(current_difficulty)

    if is_correct:
        next_index = min(current_index + 1, len(DIFFICULTY_LEVELS) - 1)
    else:
        next_index = max(current_index - 1, 0)

    return DIFFICULTY_LEVELS[next_index]
