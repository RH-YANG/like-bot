from database.schema import TargetingSet



# ========== targeting_set 테이블 SQL ==========



def insert(cur, targeting_set):
    query = '''
        INSERT INTO targeting_set (
               name
             , platform
             , goal_count
             , max_scan_count
             , max_run_minute
             , max_post_age_hour
             , max_like_count
             , language
             , is_verified_excluded
             , author_cooldown_day
        ) VALUES (
               %(name)s
             , %(platform)s
             , %(goal_count)s
             , %(max_scan_count)s
             , %(max_run_minute)s
             , %(max_post_age_hour)s
             , %(max_like_count)s
             , %(language)s
             , %(is_verified_excluded)s
             , %(author_cooldown_day)s
        )
        RETURNING id
    '''
    cur.execute(query, targeting_set.model_dump())
    targeting_set_id = cur.fetchone()['id']

    return targeting_set_id



def select_all(cur):
    query = '''
        SELECT *
          FROM targeting_set
         ORDER BY id DESC
    '''
    cur.execute(query)
    targeting_set_list = [TargetingSet.model_validate(dict(row)) for row in cur.fetchall()]

    return targeting_set_list



def select_by_id(cur, targeting_set_id):
    query = '''
        SELECT *
          FROM targeting_set
         WHERE id = %s
    '''
    cur.execute(query, (targeting_set_id,))
    row = cur.fetchone()

    targeting_set = None
    if row is not None:
        targeting_set = TargetingSet.model_validate(dict(row))

    return targeting_set



def update(cur, targeting_set):
    query = '''
        UPDATE targeting_set
           SET name = %(name)s
             , platform = %(platform)s
             , goal_count = %(goal_count)s
             , max_scan_count = %(max_scan_count)s
             , max_run_minute = %(max_run_minute)s
             , max_post_age_hour = %(max_post_age_hour)s
             , max_like_count = %(max_like_count)s
             , language = %(language)s
             , is_verified_excluded = %(is_verified_excluded)s
             , author_cooldown_day = %(author_cooldown_day)s
             , updated_at = CURRENT_TIMESTAMP
         WHERE id = %(id)s
    '''
    cur.execute(query, targeting_set.model_dump())
    updated_count = cur.rowcount

    return updated_count



def delete(cur, targeting_set_id):
    query = '''
        DELETE FROM targeting_set
         WHERE id = %s
    '''
    cur.execute(query, (targeting_set_id,))
    deleted_count = cur.rowcount

    return deleted_count
