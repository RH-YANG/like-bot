import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createRun, getRunList } from '../../api/runApi'
import { getTargetingSetList } from '../../api/targetingApi'
import { POLLING_INTERVAL_MS, RUN_END_REASON_LABEL, RUN_MODE_LABEL, RUN_STATUS_LABEL } from '../../config/label'
import { useApiData } from '../../hook/useApiData'
import { useSubmit } from '../../hook/useSubmit'
import type { RunMode } from '../../type/runType'
import { formatDateTime } from '../../util/format'
import { formatRunProgress } from '../../util/runProgress'
import s from './RunPage.module.css'



async function fetchRunList() {
  const response = await getRunList()
  return response.data.runList
}


async function fetchTargetingSetList() {
  const response = await getTargetingSetList()
  return response.data.targetingSetList
}


function RunPage() {
  // --- state
  const [targetingSetId, setTargetingSetId] = useState<number | ''>('')
  const [mode, setMode] = useState<RunMode>('auto')

  // --- hook
  const navigate = useNavigate()
  const { data: runList, error: listError } = useApiData(fetchRunList, { pollingMs: POLLING_INTERVAL_MS })
  const { data: targetingSetList } = useApiData(fetchTargetingSetList)
  const { isSubmitting, error: submitError, submit } = useSubmit()

  // --- handler
  const handleStart = async () => {
    if (targetingSetId === '') return
    let createdRunId = 0
    const isSuccess = await submit(async () => {
      const response = await createRun({ targetingSetId, mode })
      createdRunId = response.data.runId
    })
    if (isSuccess) navigate(`/run/${createdRunId}`)
  }

  return (
    <>
      <h1>실행</h1>

      <section className={s.startForm}>
        <select value={targetingSetId} onChange={(e) => setTargetingSetId(e.target.value ? Number(e.target.value) : '')}>
          <option value="">타겟팅 세트 선택</option>
          {targetingSetList?.map((targetingSet) => (
            <option key={targetingSet.id} value={targetingSet.id}>
              {targetingSet.name} (목표 {targetingSet.goalCount})
            </option>
          ))}
        </select>
        {(['auto', 'approval'] as RunMode[]).map((runMode) => (
          <label key={runMode}>
            <input type="radio" checked={mode === runMode} onChange={() => setMode(runMode)} /> {RUN_MODE_LABEL[runMode]}
          </label>
        ))}
        <button className="primary" disabled={targetingSetId === '' || isSubmitting} onClick={handleStart}>
          실행
        </button>
        {targetingSetList?.length === 0 && (
          <span className="muted">
            먼저 <Link to="/targeting-set">타겟팅 세트</Link>를 만들어 주세요.
          </span>
        )}
      </section>
      <p className="muted">
        승인 후 좋아요: 조건에 맞는 글을 목표 개수만큼 모은 뒤, 상세 화면에서 고른 글에만 좋아요를 누릅니다. 아무것도 승인하지 않고
        중지하면 미리보기로 쓸 수 있어요.
      </p>
      {submitError && <div className="error">{submitError.message}</div>}

      <h2>최근 실행</h2>
      {listError && <div className="error">{listError.message}</div>}
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>타겟팅 세트</th>
            <th>모드</th>
            <th>상태</th>
            <th>진행</th>
            <th>검토</th>
            <th>종료 이유</th>
            <th>시작</th>
            <th>종료</th>
          </tr>
        </thead>
        <tbody>
          {runList?.map((run) => (
            <tr key={run.id}>
              <td>
                <Link to={`/run/${run.id}`}>{run.id}</Link>
              </td>
              <td>{run.targetingSetName}</td>
              <td>{RUN_MODE_LABEL[run.mode]}</td>
              <td>
                <strong>{RUN_STATUS_LABEL[run.status]}</strong>
              </td>
              <td>{formatRunProgress(run)}</td>
              <td>
                {run.scannedCount}/{run.maxScanCount}
              </td>
              <td>{run.endReason ? RUN_END_REASON_LABEL[run.endReason] : '-'}</td>
              <td>{formatDateTime(run.startedAt)}</td>
              <td>{formatDateTime(run.finishedAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {runList?.length === 0 && <p className="muted">아직 실행 기록이 없어요.</p>}
    </>
  )
}


export default RunPage
