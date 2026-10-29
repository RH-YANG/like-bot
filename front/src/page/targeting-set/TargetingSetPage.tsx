import { useState } from 'react'
import { createTargetingSet, deleteTargetingSet, getTargetingSetList, updateTargetingSet } from '../../api/targetingApi'
import { LANGUAGE_LABEL } from '../../config/label'
import { useApiData } from '../../hook/useApiData'
import { useSubmit } from '../../hook/useSubmit'
import type { SaveTargetingSetRequest, TargetingSet } from '../../type/targetingSetType'
import TargetingSetForm from './TargetingSetForm'



async function fetchTargetingSetList() {
  const response = await getTargetingSetList()
  return response.data.targetingSetList
}


// 편집 대상: null이면 폼 닫힘, 'new'면 새로 만들기
type EditTarget = TargetingSet | 'new' | null


function TargetingSetPage() {
  // --- state
  const [editTarget, setEditTarget] = useState<EditTarget>(null)

  // --- hook
  const { data: targetingSetList, error: listError, reload } = useApiData(fetchTargetingSetList)
  const { isSubmitting, error: submitError, submit, clearError } = useSubmit()

  // --- handler
  const handleSave = async (request: SaveTargetingSetRequest) => {
    const isSuccess = await submit(() =>
      editTarget && editTarget !== 'new' ? updateTargetingSet(editTarget.id, request) : createTargetingSet(request),
    )
    if (!isSuccess) return
    setEditTarget(null)
    reload()
  }

  const handleDelete = async (targetingSet: TargetingSet) => {
    if (!window.confirm(`'${targetingSet.name}' 세트를 삭제할까요? 실행 기록은 남아요.`)) return
    const isSuccess = await submit(() => deleteTargetingSet(targetingSet.id))
    if (isSuccess) reload()
  }

  const handleEdit = (target: EditTarget) => {
    clearError()
    setEditTarget(target)
  }

  return (
    <>
      <h1>타겟팅 세트</h1>
      <button className="primary" onClick={() => handleEdit('new')}>
        새 세트
      </button>

      {submitError && <div className="error">{submitError.message}</div>}
      {editTarget && (
        <TargetingSetForm
          key={editTarget === 'new' ? 'new' : editTarget.id}
          targetingSet={editTarget === 'new' ? null : editTarget}
          isSubmitting={isSubmitting}
          onSubmit={handleSave}
          onCancel={() => handleEdit(null)}
        />
      )}

      <h2>목록</h2>
      {listError && <div className="error">{listError.message}</div>}
      <table>
        <thead>
          <tr>
            <th>이름</th>
            <th>언어</th>
            <th>목표/최대 검토</th>
            <th>최대 시간</th>
            <th>쿨다운</th>
            <th>기간</th>
            <th>좋아요 상한</th>
            <th>인증 제외</th>
            <th>검색어</th>
            <th>제외 키워드</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {targetingSetList?.map((targetingSet) => (
            <tr key={targetingSet.id}>
              <td>{targetingSet.name}</td>
              <td>{LANGUAGE_LABEL[targetingSet.language]}</td>
              <td>
                {targetingSet.goalCount}/{targetingSet.maxScanCount}
              </td>
              <td>{targetingSet.maxRunMinute}분</td>
              <td>{targetingSet.authorCooldownDay}일</td>
              <td>{targetingSet.maxPostAgeHour === null ? '제한 없음' : `${targetingSet.maxPostAgeHour}시간`}</td>
              <td>{targetingSet.maxLikeCount ?? '제한 없음'}</td>
              <td>{targetingSet.isVerifiedExcluded ? '예' : '아니오'}</td>
              <td>{targetingSet.searchKeywordList.join(', ')}</td>
              <td>{targetingSet.excludeKeywordList.join(', ') || '-'}</td>
              <td>
                <button onClick={() => handleEdit(targetingSet)}>수정</button>{' '}
                <button className="danger" disabled={isSubmitting} onClick={() => handleDelete(targetingSet)}>
                  삭제
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {targetingSetList?.length === 0 && <p className="muted">아직 타겟팅 세트가 없어요.</p>}
    </>
  )
}


export default TargetingSetPage
