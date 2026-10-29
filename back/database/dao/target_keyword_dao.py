from database.schema import TargetKeyword



# ========== target_keyword 테이블 SQL ==========



def insert(cur, target_keyword):
    query = '''
        INSERT INTO target_keyword (
               targeting_set_id
             , type
             , keyword
        ) VALUES (
               %(targeting_set_id)s
             , %(type)s
             , %(keyword)s
        )
        ON CONFLICT (targeting_set_id, type, keyword) DO NOTHING
    '''
    cur.execute(query, target_keyword.model_dump())



def select_by_targeting_set_id(cur, targeting_set_id):
    query = '''
        SELECT *
          FROM target_keyword
         WHERE targeting_set_id = %s
         ORDER BY id
    '''
    cur.execute(query, (targeting_set_id,))
    target_keyword_list = [TargetKeyword.model_validate(dict(row)) for row in cur.fetchall()]

    return target_keyword_list



def delete_by_targeting_set_id(cur, targeting_set_id):
    query = '''
        DELETE FROM target_keyword
         WHERE targeting_set_id = %s
    '''
    cur.execute(query, (targeting_set_id,))
