from platform_lib import load_delta_records, load_local_env, push_features_to_redis

def load_from_delta_and_push_feast():
    load_local_env()
    records = load_delta_records()
    if not records:
        print("No data in Delta Lake yet")
        return

    print(f"Loaded {len(records)} records from Delta Lake")
    stored = push_features_to_redis(records)
    print(f"Integration 3+4 OK: Delta Lake → Feast (Redis) — {stored} features stored")

load_from_delta_and_push_feast()
