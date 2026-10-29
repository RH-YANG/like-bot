import { BROWSER_VIEW_URL } from '../../config/label'
import s from './BrowserPage.module.css'



// worker가 조작하는 브라우저 화면. Threads 로그인과 진행 상황 확인에 쓴다
function BrowserPage() {
  return (
    <div className={s.page}>
      <p className={s.guide}>
        여기서 Threads에 로그인해 주세요. 로그인 상태는 컨테이너를 다시 띄워도 유지돼요. 실행 중에는 화면을 조작하지 마세요(봇
        동작이 꼬일 수 있어요).
      </p>
      <iframe className={s.frame} src={BROWSER_VIEW_URL} title="worker 브라우저 화면" />
    </div>
  )
}


export default BrowserPage
