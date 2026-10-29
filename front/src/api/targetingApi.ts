import client from './client'
import type {
  SaveTargetingSetRequest,
  SaveTargetingSetResponse,
  TargetingSetListResponse,
} from '../type/targetingSetType'



export function getTargetingSetList() {
  return client.get<TargetingSetListResponse>('/targeting')
}


export function createTargetingSet(request: SaveTargetingSetRequest) {
  return client.post<SaveTargetingSetResponse>('/targeting', request)
}


export function updateTargetingSet(targetingSetId: number, request: SaveTargetingSetRequest) {
  return client.put<SaveTargetingSetResponse>(`/targeting/${targetingSetId}`, request)
}


export function deleteTargetingSet(targetingSetId: number) {
  return client.delete(`/targeting/${targetingSetId}`)
}
