import type { Run } from '../type/runType'



// 승인 모드는 수집 단계면 후보 수, 좋아요 단계면 남은 승인 수를 함께 보여준다
export function formatRunProgress(run: Run): string {
  if (run.mode === 'approval' && run.approvedCount > 0) return `좋아요 ${run.likedCount} · 남은 승인 ${run.approvedCount}`
  const isCollecting = run.mode === 'approval' && run.likedCount === 0 && run.status !== 'finished'
  if (isCollecting) return `후보 ${run.candidateCount}/${run.goalCount}`
  return `좋아요 ${run.likedCount}/${run.goalCount}`
}


export function isRunActive(run: Run): boolean {
  return run.status !== 'finished'
}
