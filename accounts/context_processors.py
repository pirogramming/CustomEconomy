# 레벨 진행도(progress_percent, points_to_next_level)를 모든 템플릿에 제공

def level_progress(request):
    progress_percent = 0
    points_to_next_level = 0
    sidebar_dash_offset = 326.73  # 원형 진행률 ring 전체 숨김 = 0% 표시

    if getattr(request, "user", None) and request.user.is_authenticated:
        next_level_map = {1: 1715, 2: 5635, 3: 12985, 4: 25725, 5: 999999}
        prev_level_map = {1: 0, 2: 1715, 3: 5635, 4: 12985, 5: 25725}
        current_level = int(request.user.level)
        current_total_score = float(request.user.total_score or 0)
        next_xp = float(next_level_map.get(current_level, 999999))
        prev_xp = float(prev_level_map.get(current_level, 0))

        if current_level >= 5:
            progress_percent = 100
            points_to_next_level = 0
        else:
            points_to_next_level = max(0, int(next_xp - current_total_score))
            level_range = next_xp - prev_xp
            current_progress = max(0, current_total_score - prev_xp)
            if level_range > 0:
                raw = (float(current_progress) / float(level_range)) * 100
                progress_percent = min(100, int(raw))
            else:
                progress_percent = 0

        # 원형 SVG: stroke-dashoffset = 326.73 * (1 - progress_percent/100)
        sidebar_dash_offset = round(326.73 * (100 - progress_percent) / 100, 2)

    return {
        "progress_percent": progress_percent,
        "points_to_next_level": points_to_next_level,
        "sidebar_dash_offset": sidebar_dash_offset,
    }
