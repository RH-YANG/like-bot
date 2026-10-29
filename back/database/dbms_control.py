import functools
from fastapi import HTTPException, status
from psycopg2.extensions import register_adapter
from psycopg2.extras import DictCursor, Json
from psycopg2.pool import ThreadedConnectionPool

import env



# ========== DB 커넥션·커서 주입과 반환 ==========



# dict 파라미터는 jsonb 컬럼 값으로 전달한다
register_adapter(dict, Json)

connection_pool = None



def get_connection_pool():
    global connection_pool
    if connection_pool is None:
        connection_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=env.DB_HOST,
            port=env.DB_PORT,
            user=env.DB_USER,
            password=env.DB_PWD,
            dbname=env.DB_NAME,
            options='-c timezone=UTC',
        )

    return connection_pool



def connect_db(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pool = get_connection_pool()
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                func_result = func(conn, cur, *args, **kwargs)
        finally:
            # 커밋하지 않은 변경은 버리고 풀에 반환한다
            if not conn.closed:
                conn.rollback()
            pool.putconn(conn, close=bool(conn.closed))

        return func_result

    return wrapper



def db_fail_routine(conn):
    conn.rollback()
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='DB 처리에 실패했어요.')
