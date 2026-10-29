import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { approveRun, getRunDetail, stopRun } from '../../api/runApi'
import {
  POLLING_INTERVAL_MS,
  POST_STATUS_LABEL,
  RUN_END_REASON_LABEL,
  RUN_MODE_LABEL,
  RUN_STATUS_LABEL,
  SKIP_REASON_LABEL,
} from '../../config/label'
import { useApiData } from '../../hook/useApiData'
import { useSubmit } from '../../hook/useSubmit'
import { formatDateTime } from '../../util/format'
import { formatRunProgress, isRunActive } from '../../util/runProgress'
import PostCard from './PostCard'
import s from './RunDetailPage.module.css'



// 계정 상태 문제로 끝났을 때 사용자에게 보여줄 조치 안내
const ACCOUNT_ISSUE_REASON = ['login_required', 'challenge_detected', 'action_blocked']


// 사용자가 고른 승인 대상. 실행이 바뀌면 무효가 되도록 runId와 함께 둔다
interface Selection {
  runId: number
  postIdSet: Set<number>
}


function RunDetailPage() {
  // --- state
  const [selection, setSelection] = useState<Selection | null>(null)
  const [isFinished, setIsFinished] = useState(false)

  // --- hook
  const runId = Number(useParams().runId)
  const { data: detail, error: detailError, reload } = useApiData(
    async () => (await getRunDetail(runId)).data,
    { pollingMs: isFinished ? undefined : POLLING_INTERVAL_MS, reloadKey: runId },
  )
  const { isSubmitting, error: submitError, submit } = useSubmit()
  // 다른 실행으로 이동한 직후에는 이전 실행 데이터를 보여주지 않는다
  const run = detail?.run.id === runId ? detail.run : undefined
  const postList = run && detail ? detail.postList : []
  const candidateList = postList.filter((post) => post.status === 'candidate')
  const processedList = postList.filter((post) => post.status !== 'candidate')
  const isAwaitingApproval = run?.status === 'awaiting_approval'
  // 직접 고르기 전에는 후보 전체가 선택된 상태다(렌더 중 계산)
  const selectedPostId = selection?.runId === runId ? selection.postIdSet : new Set(candidateList.map((post) => post.id))

  // --- handler
  const handleStop = async () => {
    const isSuccess = await submit(() => stopRun(runId))
    if (isSuccess) reload()
  }

  const handleApprove = async () => {
    const approvedPostIdList = [...selectedPostId]
    const isSuccess = await submit(() => approveRun(runId, { approvedPostIdList }))
    if (isSuccess) reload()
  }

  const toggleCandidate = (postId: number) => {
    const next = new Set(selectedPostId)
    if (next.has(postId)) next.delete(postId)
    else next.add(postId)
    setSelection({ runId, postIdSet: next })
  }

  const toggleAllCandidate = (isSelected: boolean) => {
    setSelection({ runId, postIdSet: new Set(isSelected ? candidateList.map((post) => post.id) : []) })
  }

  // --- effect
  // 끝난 실행은 더 바뀌지 않으므로 폴링을 멈춘다
  useEffect(() => {
    setIsFinished(run?.status === 'finished')
  }, [run?.status])

  if (!run) {
    return detailError ? <div className="error">{detailError.message}</div> : <p className="muted">불러오는 중…</p>
  }

  const selectedCount = selectedPostId.size
  const skipEntryList = Object.entries(run.skipCount).sort((a, b) => b[1] - a[1])

  return (
    <>
      <p>
        <Link to="/run">← 실행 목록</Link>
      </p>
      <h1>
        실행 #{run.id} · {run.targetingSetName}
      </h1>

      <section className={s.summary}>
        <span>모드: {RUN_MODE_LABEL[run.mode]}</span>
        <span>
          상태: <strong>{RUN_STATUS_LABEL[run.status]}</strong>
        </span>
        <span>{formatRunProgress(run)}</span>
        <span>
          검토 {run.scannedCount}/{run.maxScanCount}
        </span>
        <span>종료 이유: {run.endReason ? RUN_END_REASON_LABEL[run.endReason] : '-'}</span>
        <span>시작 {formatDateTime(run.startedAt)}</span>
        <span>종료 {formatDateTime(run.finishedAt)}</span>
        <span className="muted">마지막 신호 {formatDateTime(run.heartbeatAt)}</span>
        {isRunActive(run) && run.status !== 'stopping' && (
          <button className="danger" disabled={isSubmitting} onClick={handleStop}>
            중지
          </button>
        )}
      </section>

      {run.endReason && ACCOUNT_ISSUE_REASON.includes(run.endReason) && (
        <div className="notice">
          계정 상태 때문에 멈췄어요.{' '}
          <Link to="/browser">브라우저 화면</Link>
          에서 Threads에 로그인하거나 안내를 확인한 뒤 다시 실행해 주세요. 활동 제한이면 하루 이상 쉬는 걸 권해요.
        </div>
      )}
      {run.errorMessage && <div className="error pre">{run.errorMessage}</div>}
      {detailError && <div className="error">{detailError.message}</div>}
      {submitError && <div className="error">{submitError.message}</div>}

      {isAwaitingApproval && (
        <section>
          <h2>승인할 후보 ({selectedCount}/{candidateList.length} 선택)</h2>
          <div className={s.approveBar}>
            <button onClick={() => toggleAllCandidate(true)}>모두 선택</button>
            <button onClick={() => toggleAllCandidate(false)}>모두 해제</button>
            <button className="primary" disabled={isSubmitting} onClick={handleApprove}>
              선택한 {selectedCount}개에 좋아요 실행
            </button>
            <span className="muted">선택하지 않은 후보는 거절되어 이후 실행에서도 제외돼요.</span>
          </div>
          <div className={s.cardList}>
            {candidateList.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                isSelected={selectedPostId.has(post.id)}
                onToggle={() => toggleCandidate(post.id)}
              />
            ))}
          </div>
        </section>
      )}

      <h2>건너뛴 이유</h2>
      {skipEntryList.length === 0 ? (
        <p className="muted">없음</p>
      ) : (
        <table className={s.skipTable}>
          <tbody>
            {skipEntryList.map(([skipReason, count]) => (
              <tr key={skipReason}>
                <th>{SKIP_REASON_LABEL[skipReason] ?? skipReason}</th>
                <td>{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>처리한 게시글 ({processedList.length})</h2>
      <table>
        <thead>
          <tr>
            <th>상태</th>
            <th>작성자</th>
            <th>본문</th>
            <th>검색어</th>
            <th>좋아요 시각</th>
          </tr>
        </thead>
        <tbody>
          {processedList.map((post) => (
            <tr key={post.id}>
              <td>{POST_STATUS_LABEL[post.status]}</td>
              <td>@{post.authorHandle}</td>
              <td className="pre">
                <a href={post.url} target="_blank" rel="noreferrer">
                  {post.content ?? '(본문 없음)'}
                </a>
              </td>
              <td>{post.searchKeyword}</td>
              <td>{formatDateTime(post.likedAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}


export default RunDetailPage
