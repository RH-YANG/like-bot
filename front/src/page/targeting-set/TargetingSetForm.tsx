import { useState } from 'react'
import { LANGUAGE_LABEL } from '../../config/label'
import type { Language, SaveTargetingSetRequest, TargetingSet } from '../../type/targetingSetType'
import { parseKeywordText } from '../../util/format'
import s from './TargetingSetForm.module.css'



interface TargetingSetFormProps {
  targetingSet: TargetingSet | null      // null이면 새로 만들기
  isSubmitting: boolean
  onSubmit: (request: SaveTargetingSetRequest) => void
  onCancel: () => void
}


interface FormValue {
  name: string
  goalCount: string
  maxScanCount: string
  maxRunMinute: string
  maxPostAgeHour: string
  maxLikeCount: string
  language: Language
  isVerifiedExcluded: boolean
  authorCooldownDay: string
  searchKeywordText: string
  excludeKeywordText: string
}


const DEFAULT_FORM_VALUE: FormValue = {
  name: '',
  goalCount: '50',
  maxScanCount: '500',
  maxRunMinute: '150',
  maxPostAgeHour: '72',
  maxLikeCount: '',
  language: 'ko',
  isVerifiedExcluded: true,
  authorCooldownDay: '14',
  searchKeywordText: '',
  excludeKeywordText: '',
}


function toFormValue(targetingSet: TargetingSet | null): FormValue {
  if (!targetingSet) return DEFAULT_FORM_VALUE
  return {
    name: targetingSet.name,
    goalCount: String(targetingSet.goalCount),
    maxScanCount: String(targetingSet.maxScanCount),
    maxRunMinute: String(targetingSet.maxRunMinute),
    maxPostAgeHour: targetingSet.maxPostAgeHour === null ? '' : String(targetingSet.maxPostAgeHour),
    maxLikeCount: targetingSet.maxLikeCount === null ? '' : String(targetingSet.maxLikeCount),
    language: targetingSet.language,
    isVerifiedExcluded: targetingSet.isVerifiedExcluded,
    authorCooldownDay: String(targetingSet.authorCooldownDay),
    searchKeywordText: targetingSet.searchKeywordList.join('\n'),
    excludeKeywordText: targetingSet.excludeKeywordList.join('\n'),
  }
}


// 빈 칸은 '제한 없음'(null)으로 보낸다
function toNullableNumber(text: string): number | null {
  return text.trim() === '' ? null : Number(text)
}


function TargetingSetForm({ targetingSet, isSubmitting, onSubmit, onCancel }: TargetingSetFormProps) {
  // --- state
  const [formValue, setFormValue] = useState<FormValue>(() => toFormValue(targetingSet))

  // --- handler
  const handleChange = <K extends keyof FormValue>(key: K, value: FormValue[K]) => {
    setFormValue((current) => ({ ...current, [key]: value }))
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    onSubmit({
      name: formValue.name,
      platform: 'threads',
      goalCount: Number(formValue.goalCount),
      maxScanCount: Number(formValue.maxScanCount),
      maxRunMinute: Number(formValue.maxRunMinute),
      maxPostAgeHour: toNullableNumber(formValue.maxPostAgeHour),
      maxLikeCount: toNullableNumber(formValue.maxLikeCount),
      language: formValue.language,
      isVerifiedExcluded: formValue.isVerifiedExcluded,
      authorCooldownDay: Number(formValue.authorCooldownDay),
      searchKeywordList: parseKeywordText(formValue.searchKeywordText),
      excludeKeywordList: parseKeywordText(formValue.excludeKeywordText),
    })
  }

  return (
    <form className={s.form} onSubmit={handleSubmit}>
      <h2>{targetingSet ? `세트 수정: ${targetingSet.name}` : '새 타겟팅 세트'}</h2>

      <label className={s.field}>
        <span>이름</span>
        <input value={formValue.name} onChange={(e) => handleChange('name', e.target.value)} required />
      </label>
      <label className={s.field}>
        <span>플랫폼</span>
        <select value="threads" disabled>
          <option value="threads">Threads</option>
        </select>
      </label>
      <label className={s.field}>
        <span>대상 언어</span>
        <select value={formValue.language} onChange={(e) => handleChange('language', e.target.value as Language)}>
          {(Object.keys(LANGUAGE_LABEL) as Language[]).map((language) => (
            <option key={language} value={language}>
              {LANGUAGE_LABEL[language]}
            </option>
          ))}
        </select>
      </label>
      <label className={s.field}>
        <span>목표 좋아요 수</span>
        <input type="number" min={1} value={formValue.goalCount} onChange={(e) => handleChange('goalCount', e.target.value)} />
      </label>
      <label className={s.field}>
        <span>최대 검토 게시글 수</span>
        <input type="number" min={1} value={formValue.maxScanCount} onChange={(e) => handleChange('maxScanCount', e.target.value)} />
      </label>
      <label className={s.field}>
        <span>최대 실행 시간(분)</span>
        <input type="number" min={1} value={formValue.maxRunMinute} onChange={(e) => handleChange('maxRunMinute', e.target.value)} />
      </label>
      <label className={s.field}>
        <span>작성자 쿨다운(일)</span>
        <input
          type="number"
          min={0}
          title="같은 작성자에게 다시 좋아요하기까지 최소 일수"
          value={formValue.authorCooldownDay}
          onChange={(e) => handleChange('authorCooldownDay', e.target.value)}
        />
      </label>
      <label className={s.field}>
        <span>게시 후 몇 시간 이내</span>
        <input
          type="number"
          min={1}
          placeholder="비우면 제한 없음"
          value={formValue.maxPostAgeHour}
          onChange={(e) => handleChange('maxPostAgeHour', e.target.value)}
        />
      </label>
      <label className={s.field}>
        <span>게시글 좋아요 수 상한</span>
        <input
          type="number"
          min={0}
          placeholder="비우면 제한 없음"
          value={formValue.maxLikeCount}
          onChange={(e) => handleChange('maxLikeCount', e.target.value)}
        />
      </label>
      <label className={s.check}>
        <input
          type="checkbox"
          checked={formValue.isVerifiedExcluded}
          onChange={(e) => handleChange('isVerifiedExcluded', e.target.checked)}
        />
        인증 배지 계정 제외
      </label>
      <label className={s.field}>
        <span>검색어 (줄바꿈 또는 쉼표로 구분)</span>
        <textarea rows={5} value={formValue.searchKeywordText} onChange={(e) => handleChange('searchKeywordText', e.target.value)} />
      </label>
      <label className={s.field}>
        <span>제외 키워드 (본문에 있으면 건너뜀)</span>
        <textarea rows={5} value={formValue.excludeKeywordText} onChange={(e) => handleChange('excludeKeywordText', e.target.value)} />
      </label>

      <div className={s.buttonRow}>
        <button type="submit" className="primary" disabled={isSubmitting}>
          저장
        </button>
        <button type="button" onClick={onCancel}>
          취소
        </button>
      </div>
    </form>
  )
}


export default TargetingSetForm
