from fastapi import FastAPI

import api.targeting_api as targeting_api
import api.run_api as run_api
import api.post_api as post_api
import api.author_api as author_api



# ========== 앱 초기화와 라우터 등록 ==========



app = FastAPI(title='like-bot')

app.include_router(targeting_api.router)
app.include_router(run_api.router)
app.include_router(post_api.router)
app.include_router(author_api.router)
