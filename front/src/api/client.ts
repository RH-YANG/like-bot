import axios from 'axios'



// 모든 API 호출이 쓰는 공통 인스턴스. Vite가 /api를 back으로 프록시한다
const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
  paramsSerializer: { indexes: null },
})


export default client
