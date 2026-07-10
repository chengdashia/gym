def recent_unique_records(rows: list, limit: int = 10) -> list:
    seen = set()
    result = []
    for row in rows:
        key = (row.food_source, row.food_id, row.custom_food_id, row.food_name_snapshot)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
        if len(result) >= limit:
            break
    return result
