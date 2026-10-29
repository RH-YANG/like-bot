const DATE_TIME_FORMAT = new Intl.DateTimeFormat('ko-KR', {
  timeZone: 'Asia/Seoul',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})


// 서버의 UTC 시각을 한국 시간으로 표시한다
export function formatDateTime(value: string | null): string {
  if (!value) return '-'
  return DATE_TIME_FORMAT.format(new Date(value))
}


export function parseKeywordText(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((keyword) => keyword.trim())
    .filter((keyword) => keyword !== '')
}
