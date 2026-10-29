import client from './client'
import type {
  ApproveRunRequest,
  CreateRunRequest,
  CreateRunResponse,
  RunDetailResponse,
  RunListResponse,
} from '../type/runType'



export function getRunList() {
  return client.get<RunListResponse>('/run')
}


export function getRunDetail(runId: number) {
  return client.get<RunDetailResponse>(`/run/${runId}`)
}


export function createRun(request: CreateRunRequest) {
  return client.post<CreateRunResponse>('/run', request)
}


export function stopRun(runId: number) {
  return client.post(`/run/${runId}/stop`)
}


export function approveRun(runId: number, request: ApproveRunRequest) {
  return client.post(`/run/${runId}/approval`, request)
}
