import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './component/Layout'
import RunPage from './page/run/RunPage'
import RunDetailPage from './page/run-detail/RunDetailPage'
import TargetingSetPage from './page/targeting-set/TargetingSetPage'
import PostPage from './page/post/PostPage'
import AuthorPage from './page/author/AuthorPage'
import BrowserPage from './page/browser/BrowserPage'
import './App.css'



function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/run" replace />} />
        <Route path="/run" element={<RunPage />} />
        <Route path="/run/:runId" element={<RunDetailPage />} />
        <Route path="/targeting-set" element={<TargetingSetPage />} />
        <Route path="/post" element={<PostPage />} />
        <Route path="/author" element={<AuthorPage />} />
        <Route path="/browser" element={<BrowserPage />} />
      </Route>
    </Routes>
  )
}


export default App
