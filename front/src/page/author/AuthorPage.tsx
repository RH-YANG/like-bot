import { useState } from 'react'
import { getAuthorList, updateAuthor } from '../../api/authorApi'
import { useApiData } from '../../hook/useApiData'
import { useSubmit } from '../../hook/useSubmit'
import type { Author } from '../../type/authorType'
import { formatDateTime } from '../../util/format'
import s from './AuthorPage.module.css'



function AuthorPage() {
  // --- state
  const [isBlockedOnly, setIsBlockedOnly] = useState(false)
  const [memoDraft, setMemoDraft] = useState<Record<number, string>>({})

  // --- hook
  const { data: authorList, error: listError, reload } = useApiData(
    async () => (await getAuthorList(isBlockedOnly)).data.authorList,
    { reloadKey: isBlockedOnly },
  )
  const { isSubmitting, error: submitError, submit } = useSubmit()

  // --- handler
  const handleToggleBlock = async (author: Author) => {
    const isSuccess = await submit(() => updateAuthor(author.id, { isBlocked: !author.isBlocked }))
    if (isSuccess) reload()
  }

  const handleSaveMemo = async (author: Author) => {
    const memo = memoDraft[author.id] ?? author.memo ?? ''
    const isSuccess = await submit(() => updateAuthor(author.id, { isBlocked: author.isBlocked, memo }))
    if (!isSuccess) return
    setMemoDraft((current) => {
      const next = { ...current }
      delete next[author.id]
      return next
    })
    reload()
  }

  return (
    <>
      <h1>작성자</h1>
      <label className={s.filter}>
        <input type="checkbox" checked={isBlockedOnly} onChange={(e) => setIsBlockedOnly(e.target.checked)} /> 제외 계정만 보기
      </label>
      <p className="muted">제외한 계정의 글은 다음 실행부터 건너뛰어요. 좋아요 대상으로 판정된 글의 작성자만 목록에 나와요.</p>

      {listError && <div className="error">{listError.message}</div>}
      {submitError && <div className="error">{submitError.message}</div>}
      <table>
        <thead>
          <tr>
            <th>계정</th>
            <th>인증</th>
            <th>좋아요한 글</th>
            <th>마지막 좋아요</th>
            <th>제외</th>
            <th>메모</th>
          </tr>
        </thead>
        <tbody>
          {authorList?.map((author) => {
            const memo = memoDraft[author.id] ?? author.memo ?? ''
            const isMemoChanged = memoDraft[author.id] !== undefined && memoDraft[author.id] !== (author.memo ?? '')
            return (
              <tr key={author.id}>
                <td>
                  <a href={author.url} target="_blank" rel="noreferrer">
                    @{author.handle}
                  </a>
                  {author.displayName && <span className="muted"> {author.displayName}</span>}
                </td>
                <td>{author.isVerified ? '✔' : ''}</td>
                <td>{author.likedPostCount}</td>
                <td>{formatDateTime(author.lastLikedAt)}</td>
                <td>
                  <button className={author.isBlocked ? '' : 'danger'} disabled={isSubmitting} onClick={() => handleToggleBlock(author)}>
                    {author.isBlocked ? '제외 해제' : '제외'}
                  </button>
                </td>
                <td className={s.memo}>
                  <input
                    value={memo}
                    placeholder="메모"
                    onChange={(e) => setMemoDraft((current) => ({ ...current, [author.id]: e.target.value }))}
                  />
                  <button disabled={!isMemoChanged || isSubmitting} onClick={() => handleSaveMemo(author)}>
                    저장
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {authorList?.length === 0 && <p className="muted">해당하는 작성자가 없어요.</p>}
    </>
  )
}


export default AuthorPage
