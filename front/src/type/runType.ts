import type { Platform } from './targetingSetType'
import type { Post } from './postType'


export type RunMode = 'auto' | 'approval'
export type RunStatus = 'pending' | 'running' | 'awaiting_approval' | 'stopping' | 'finished'
export type RunEndReason =
  | 'goal_reached'
  | 'search_exhausted'
  | 'max_scan_reached'
  | 'max_duration_reached'
  | 'limit_reached'
  | 'none_approved'
  | 'user_stopped'
  | 'login_required'
  | 'challenge_detected'
  | 'action_blocked'
  | 'interrupted'
  | 'error'


export interface Run {
  id: number
  targetingSetId: number | null
  targetingSetName: string
  platform: Platform
  mode: RunMode
  status: RunStatus
  endReason: RunEndReason | null
  goalCount: number
  maxScanCount: number
  scannedCount: number
  likedCount: number
  candidateCount: number
  approvedCount: number
  skipCount: Record<string, number>
  errorMessage: string | null
  heartbeatAt: string | null
  startedAt: string | null
  finishedAt: string | null
  createdAt: string
}


export interface RunListResponse {
  runList: Run[]
}


export interface RunDetailResponse {
  run: Run
  postList: Post[]
}


export interface CreateRunRequest {
  targetingSetId: number
  mode: RunMode
}


export interface CreateRunResponse {
  runId: number
}


export interface ApproveRunRequest {
  approvedPostIdList: number[]
}
