/** 与 backend/ai_service.py 的 glance_line 保持一致 */
const GLANCE_LABEL = {
  折叠伞: '带伞',
  薄外套: '加外套',
  围巾: '围巾',
  防晒: '防晒',
  简历: '带简历',
  水杯: '水杯',
  校园卡: '校园卡',
  充电宝: '充电宝',
  纸巾: '纸巾',
  防滑鞋: '防滑',
}

const OCCASION_SHORT = {
  日常上课: '上课',
  约会: '约会',
  运动健身: '运动',
  面试答辩: '面试',
  周末出游: '出游',
  聚会派对: '聚会',
}

export function glanceLine(brings, occasion, outfitTitle = '') {
  const parts = []
  if (brings?.[0]) {
    const label = brings[0].label
    parts.push(GLANCE_LABEL[label] || label)
  }
  parts.push(OCCASION_SHORT[occasion] || (occasion || '日常').slice(0, 2))
  const title = (outfitTitle || '').split('·')[0].trim()
  if (title) parts.push(title.slice(0, 6))
  return parts.join(' · ')
}
