import { useState } from 'react'
import { Link } from 'react-router-dom'
import { updateAuthor } from '../../api/authorApi'
import { getPostList } from '../../api/postApi'
import { POST_STATUS_LABEL } from '../../config/label'
import { useApiData } from '../../hook/useApiData'
import { useSubmit } from '../../hook/useSubmit'
import type { Post, PostStatus } from '../../type/postType'
import { formatDateTime } from '../../util/format'
import s from './PostPage.module.css'



const STATUS_FILTER_LIST: { label: string; statusList: PostStatus[] }[] = [
  { label: '좋아요', statusList: ['liked'] },
  { label: '실패', statusList: ['failed'] },
  { label: '승인 대기 후보', statusList: ['candidate', 'approved'] },
  { label: '거절', statusList: ['rejected'] },
  { label: '전체', statusList: [] },
]


function PostPage() {
  // --- state
  const [filterIndex, setFilterIndex] = useState(0)

  // --- hook
  const statusList = STATUS_FILTER_LIST[filterIndex].statusList
  const { data: postList, error: listError, reload } = useApiData(
    async () => (await getPostList(statusList)).data.postList,
    { reloadKey: filterIndex },
  )
  const { isSubmitting, error: submitError, submit } = useSubmit()

  // --- handler
  // 메모는 보내지 않아 기존 메모를 유지한다
  const handleToggleBlock = async (post: Post) => {
    const isSuccess = await submit(() => updateAuthor(post.authorId, { isBlocked: !post.isAuthorBlocked }))
    if (isSuccess) reload()
  }

  return (
    <>
      <h1>게시글</h1>
      <div className={s.filter}>
        {STATUS_FILTER_LIST.map((filter, index) => (
          <button key={filter.label} className={index === filterIndex ? 'primary' : ''} onClick={() => setFilterIndex(index)}>
            {filter.label}
          </button>
        ))}
        <span className="muted">최근 200건</span>
      </div>

      {listError && <div className="error">{listError.message}</div>}
      {submitError && <div className="error">{submitError.message}</div>}
      <table>
        <thead>
          <tr>
            <th>시각</th>
            <th>상태</th>
            <th>작성자</th>
            <th>본문</th>
            <th>검색어</th>
            <th>당시 좋아요</th>
            <th>실행</th>
          </tr>
        </thead>
        <tbody>
          {postList?.map((post) => (
            <tr key={post.id}>
              <td>{formatDateTime(post.likedAt ?? post.createdAt)}</td>
              <td>{POST_STATUS_LABEL[post.status]}</td>
              <td className={s.author}>
                @{post.authorHandle}
                <button
                  className={post.isAuthorBlocked ? '' : 'danger'}
                  disabled={isSubmitting}
                  onClick={() => handleToggleBlock(post)}
                >
                  {post.isAuthorBlocked ? '제외 해제' : '제외'}
                </button>
              </td>
              <td className="pre">
                <a href={post.url} target="_blank" rel="noreferrer">
                  {post.content ?? '(본문 없음)'}
                </a>
              </td>
              <td>{post.searchKeyword}</td>
              <td>{post.likeCount ?? '-'}</td>
              <td>
                <Link to={`/run/${post.runId}`}>#{post.runId}</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {postList?.length === 0 && <p className="muted">해당하는 게시글이 없어요.</p>}
    </>
  )
}


export default PostPage
