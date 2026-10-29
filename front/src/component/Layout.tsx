import { NavLink, Outlet } from 'react-router-dom'
import { getLikeUsageList } from '../api/postApi'
import { LIKE_USAGE_POLLING_INTERVAL_MS } from '../config/label'
import { useApiData } from '../hook/useApiData'
import s from './Layout.module.css'



const MENU_LIST = [
  { path: '/run', label: '실행' },
  { path: '/targeting-set', label: '타겟팅 세트' },
  { path: '/post', label: '게시글' },
  { path: '/author', label: '작성자' },
  { path: '/browser', label: '브라우저(로그인)' },
]


async function fetchLikeUsageList() {
  const response = await getLikeUsageList()
  return response.data.likeUsageList
}


function Layout() {
  // --- hook
  const { data: likeUsageList } = useApiData(fetchLikeUsageList, { pollingMs: LIKE_USAGE_POLLING_INTERVAL_MS })

  return (
    <div className={s.layout}>
      <header className={s.header}>
        <strong className={s.logo}>like-bot</strong>
        <nav className={s.nav}>
          {MENU_LIST.map((menu) => (
            <NavLink key={menu.path} to={menu.path} className={({ isActive }) => `${s.menu} ${isActive ? s.active : ''}`}>
              {menu.label}
            </NavLink>
          ))}
        </nav>
        <div className={s.status}>
          {likeUsageList?.map((likeUsage) => (
            <span key={likeUsage.platform} title="최근 24시간 / 최근 1시간 좋아요 수">
              {likeUsage.platform} 오늘 {likeUsage.dailyLikedCount}/{likeUsage.dailyLikeLimit} · 1시간{' '}
              {likeUsage.hourlyLikedCount}/{likeUsage.hourlyLikeLimit}
            </span>
          ))}
        </div>
      </header>
      <main className={s.main}>
        <Outlet />
      </main>
    </div>
  )
}


export default Layout
