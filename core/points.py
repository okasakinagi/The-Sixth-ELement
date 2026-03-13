DIFFICULTY_REWARD_MAP = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
}


def normalize_difficulty(difficulty):
    try:
        level = int(difficulty)
    except (TypeError, ValueError):
        level = 3
    if level < 1:
        return 1
    if level > 5:
        return 5
    return level


def reward_points_for_difficulty(difficulty):
    return DIFFICULTY_REWARD_MAP[normalize_difficulty(difficulty)]


def difficulty_levels_for_min_reward(min_reward):
    try:
        threshold = int(min_reward)
    except (TypeError, ValueError):
        threshold = 0
    return [
        level
        for level, reward in DIFFICULTY_REWARD_MAP.items()
        if reward >= threshold
    ]