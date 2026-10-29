from database.schema import Author



# ========== author 테이블 SQL ==========



def upsert(cur, author):
    query = '''
        INSERT INTO author (
               platform
             , handle
             , display_name
             , is_verified
        ) VALUES (
               %(platform)s
             , %(handle)s
             , %(display_name)s
             , %(is_verified)s
        )
        ON CONFLICT (platform, handle) DO UPDATE
           SET display_name = COALESCE(EXCLUDED.display_name, author.display_name)
             , is_verified = EXCLUDED.is_verified
             , updated_at = CURRENT_TIMESTAMP
        RETURNING id
    '''
    cur.execute(query, author.model_dump())
    author_id = cur.fetchone()['id']

    return author_id



def select_by_handle(cur, platform, handle):
    query = '''
        SELECT *
          FROM author
         WHERE platform = %s
           AND handle = %s
    '''
    cur.execute(query, (platform, handle))
    row = cur.fetchone()

    author = None
    if row is not None:
        author = Author.model_validate(dict(row))

    return author



def select_by_id(cur, author_id):
    query = '''
        SELECT *
          FROM author
         WHERE id = %s
    '''
    cur.execute(query, (author_id,))
    row = cur.fetchone()

    author = None
    if row is not None:
        author = Author.model_validate(dict(row))

    return author



def select_list_with_like_stat(cur, is_blocked_only, limit):
    query = '''
        SELECT a.*
             , COUNT(p.id) FILTER (WHERE p.status = 'liked') AS liked_post_count
             , MAX(p.liked_at) AS last_liked_at
          FROM author a
          LEFT JOIN post p
            ON p.author_id = a.id
         WHERE (%s = false OR a.is_blocked = true)
         GROUP BY a.id
         ORDER BY MAX(p.liked_at) DESC NULLS LAST
                , a.id DESC
         LIMIT %s
    '''
    cur.execute(query, (is_blocked_only, limit))
    author_row_list = [dict(row) for row in cur.fetchall()]

    return author_row_list



def update_manage_field(cur, author_id, is_blocked, memo):
    query = '''
        UPDATE author
           SET is_blocked = %s
             , memo = %s
             , updated_at = CURRENT_TIMESTAMP
         WHERE id = %s
    '''
    cur.execute(query, (is_blocked, memo, author_id))
    updated_count = cur.rowcount

    return updated_count
