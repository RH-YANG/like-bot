from database.schema import Post



# ========== post 테이블 SQL ==========



def insert(cur, post):
    query = '''
        INSERT INTO post (
               run_id
             , author_id
             , platform
             , post_code
             , content
             , posted_at
             , like_count
             , search_keyword
             , status
             , liked_at
        ) VALUES (
               %(run_id)s
             , %(author_id)s
             , %(platform)s
             , %(post_code)s
             , %(content)s
             , %(posted_at)s
             , %(like_count)s
             , %(search_keyword)s
             , %(status)s
             , %(liked_at)s
        )
        RETURNING id
    '''
    cur.execute(query, post.model_dump())
    post_id = cur.fetchone()['id']

    return post_id



def select_by_code(cur, platform, post_code):
    query = '''
        SELECT *
          FROM post
         WHERE platform = %s
           AND post_code = %s
    '''
    cur.execute(query, (platform, post_code))
    row = cur.fetchone()

    post = None
    if row is not None:
        post = Post.model_validate(dict(row))

    return post



def select_with_author(cur, run_id, status_list, limit):
    # run_id·status_list가 None이면 해당 조건을 적용하지 않는다
    query = '''
        SELECT p.*
             , a.handle AS author_handle
             , a.display_name AS author_display_name
             , a.is_blocked AS is_author_blocked
          FROM post p
          JOIN author a
            ON a.id = p.author_id
         WHERE (%s::integer IS NULL OR p.run_id = %s)
           AND (%s::varchar[] IS NULL OR p.status = ANY(%s))
         ORDER BY COALESCE(p.liked_at, p.created_at) DESC
                , p.id DESC
         LIMIT %s
    '''
    cur.execute(query, (run_id, run_id, status_list, status_list, limit))
    post_row_list = [dict(row) for row in cur.fetchall()]

    return post_row_list



def select_by_run_status(cur, run_id, status):
    query = '''
        SELECT p.*
             , a.handle AS author_handle
          FROM post p
          JOIN author a
            ON a.id = p.author_id
         WHERE p.run_id = %s
           AND p.status = %s
         ORDER BY p.id
    '''
    cur.execute(query, (run_id, status))
    post_row_list = [dict(row) for row in cur.fetchall()]

    return post_row_list



def count_by_run_status(cur, run_id, status):
    query = '''
        SELECT COUNT(*) AS post_count
          FROM post
         WHERE run_id = %s
           AND status = %s
    '''
    cur.execute(query, (run_id, status))
    post_count = cur.fetchone()['post_count']

    return post_count



def count_liked_since(cur, platform, since_second):
    query = '''
        SELECT COUNT(*) AS liked_count
          FROM post
         WHERE platform = %s
           AND status = 'liked'
           AND liked_at > CURRENT_TIMESTAMP - make_interval(secs => %s)
    '''
    cur.execute(query, (platform, since_second))
    liked_count = cur.fetchone()['liked_count']

    return liked_count



def count_author_recent(cur, author_id, since_second):
    # 쿨다운 기간 내 좋아요했거나, 아직 좋아요 대기 중인 같은 작성자의 글 수
    query = '''
        SELECT COUNT(*) AS post_count
          FROM post
         WHERE author_id = %s
           AND (
                   (status = 'liked' AND liked_at > CURRENT_TIMESTAMP - make_interval(secs => %s))
                OR status IN ('candidate', 'approved')
               )
    '''
    cur.execute(query, (author_id, since_second))
    post_count = cur.fetchone()['post_count']

    return post_count



def update_status(cur, post_id, from_status_list, to_status):
    query = '''
        UPDATE post
           SET status = %s
             , liked_at = CASE WHEN %s = 'liked' THEN CURRENT_TIMESTAMP ELSE liked_at END
             , updated_at = CURRENT_TIMESTAMP
         WHERE id = %s
           AND status = ANY(%s)
    '''
    cur.execute(query, (to_status, to_status, post_id, list(from_status_list)))
    updated_count = cur.rowcount

    return updated_count



def update_run_candidate(cur, run_id, approved_post_id_list):
    # 승인 목록에 있는 후보는 approved, 나머지 후보는 rejected로 바꾼다
    query = '''
        UPDATE post
           SET status = CASE WHEN id = ANY(%s) THEN 'approved' ELSE 'rejected' END
             , updated_at = CURRENT_TIMESTAMP
         WHERE run_id = %s
           AND status = 'candidate'
    '''
    cur.execute(query, (list(approved_post_id_list), run_id))



def delete_by_run_status(cur, run_id, status):
    query = '''
        DELETE FROM post
         WHERE run_id = %s
           AND status = %s
    '''
    cur.execute(query, (run_id, status))
    deleted_count = cur.rowcount

    return deleted_count
