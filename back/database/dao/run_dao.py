from database.schema import Run



# ========== run 테이블 SQL ==========



def insert(cur, run):
    query = '''
        INSERT INTO run (
               targeting_set_id
             , platform
             , mode
             , status
             , targeting_snapshot
        ) VALUES (
               %(targeting_set_id)s
             , %(platform)s
             , %(mode)s
             , %(status)s
             , %(targeting_snapshot)s
        )
        RETURNING id
    '''
    cur.execute(query, run.model_dump())
    run_id = cur.fetchone()['id']

    return run_id



def select_by_id(cur, run_id, is_for_update=False):
    query = '''
        SELECT *
          FROM run
         WHERE id = %s
    '''
    if is_for_update:
        query += ' FOR UPDATE'
    cur.execute(query, (run_id,))
    row = cur.fetchone()

    run = None
    if row is not None:
        run = Run.model_validate(dict(row))

    return run



def select_with_post_count(cur, run_id, limit):
    # 실행과 승인 대기 후보·승인 글 수. run_id가 None이면 최근 limit건
    query = '''
        SELECT r.*
             , COUNT(p.id) FILTER (WHERE p.status = 'candidate') AS candidate_count
             , COUNT(p.id) FILTER (WHERE p.status = 'approved') AS approved_count
          FROM run r
          LEFT JOIN post p
            ON p.run_id = r.id
         WHERE (%s::integer IS NULL OR r.id = %s)
         GROUP BY r.id
         ORDER BY r.id DESC
         LIMIT %s
    '''
    cur.execute(query, (run_id, run_id, limit))
    run_row_list = [dict(row) for row in cur.fetchall()]

    return run_row_list



def claim_pending(cur):
    query = '''
        UPDATE run
           SET status = 'running'
             , started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
             , heartbeat_at = CURRENT_TIMESTAMP
         WHERE id = (
                    SELECT id
                      FROM run
                     WHERE status = 'pending'
                     ORDER BY id
                     LIMIT 1
                       FOR UPDATE SKIP LOCKED
               )
           AND status = 'pending'
        RETURNING *
    '''
    cur.execute(query)
    row = cur.fetchone()

    run = None
    if row is not None:
        run = Run.model_validate(dict(row))

    return run



def update_status(cur, run_id, from_status_list, to_status):
    query = '''
        UPDATE run
           SET status = %s
         WHERE id = %s
           AND status = ANY(%s)
    '''
    cur.execute(query, (to_status, run_id, list(from_status_list)))
    updated_count = cur.rowcount

    return updated_count



def update_heartbeat(cur, run_id):
    query = '''
        UPDATE run
           SET heartbeat_at = CURRENT_TIMESTAMP
         WHERE id = %s
        RETURNING status
    '''
    cur.execute(query, (run_id,))
    row = cur.fetchone()

    run_status = None
    if row is not None:
        run_status = row['status']

    return run_status



def update_progress(cur, run_id, scanned_count, liked_count, skip_count):
    query = '''
        UPDATE run
           SET scanned_count = %s
             , liked_count = %s
             , skip_count = %s
             , heartbeat_at = CURRENT_TIMESTAMP
         WHERE id = %s
    '''
    cur.execute(query, (scanned_count, liked_count, skip_count, run_id))



def finish(cur, run_id, from_status_list, end_reason, error_message):
    query = '''
        UPDATE run
           SET status = 'finished'
             , end_reason = %s
             , error_message = %s
             , finished_at = CURRENT_TIMESTAMP
         WHERE id = %s
           AND status = ANY(%s)
    '''
    cur.execute(query, (end_reason, error_message, run_id, list(from_status_list)))
    updated_count = cur.rowcount

    return updated_count



def finish_stale(cur, status_list, stale_second, end_reason):
    # heartbeat가 stale_second 이상 끊긴 실행을 종료한다. stale_second가 0이면 해당 상태를 모두 종료한다
    query = '''
        UPDATE run
           SET status = 'finished'
             , end_reason = %s
             , finished_at = CURRENT_TIMESTAMP
         WHERE status = ANY(%s)
           AND COALESCE(heartbeat_at, created_at) <= CURRENT_TIMESTAMP - make_interval(secs => %s)
        RETURNING id
    '''
    cur.execute(query, (end_reason, list(status_list), stale_second))
    finished_run_id_list = [row['id'] for row in cur.fetchall()]

    return finished_run_id_list
