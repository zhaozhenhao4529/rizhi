import { Link } from 'react-router-dom'

const rows = [
  ['赛道', '智能日常。让手机理解今天，而不是停在对话框里。'],
  ['早晨', '出门卡把天气、场合和已有衣橱收成一套，并写明要带的东西。'],
  ['白天', '随手一拍衣柜、书包、桌面或门口。端侧先取主色，云端 Qwen-VL 可读画面；没有 Key 时用本地规则对照衣橱。'],
  ['晚上', '一日页只复述你确认穿过的衣服和拍过的画面，并留下明天第一句。'],
  ['腕上', '同一句话可以放到表盘或胸针上。初赛用手机里的圆表盘演示，决赛再接真设备。'],
  ['端云', '主色和离线搭配在本机；有阿里云 Key 时，识衣、搭配和读图走 Qwen / Qwen-VL。'],
]

export default function About() {
  return (
    <div className="animate-fade-in px-4 pt-6 pb-10">
      <p className="text-soft text-xs">天猫 AI 黑客松 · 高校挑战赛</p>
      <h1 className="font-display text-2xl font-bold tracking-wide mt-1">日知</h1>
      <p className="text-[14px] leading-relaxed mt-3 text-ink/85">
        手机自己知道你今天要过什么样的一天。你不用打字提问，点一次「今天就穿这套」，再随手拍一眼，晚上就能翻开这一页。
      </p>

      <dl className="mt-5 flex flex-col gap-3">
        {rows.map(([k, v]) => (
          <div key={k} className="p-3.5 rounded-2xl bg-card border border-sand">
            <dt className="text-[11px] text-soft tracking-wide">{k}</dt>
            <dd className="text-[13px] leading-relaxed mt-1">{v}</dd>
          </div>
        ))}
      </dl>

      <p className="text-[12px] text-soft leading-relaxed mt-4">
        特别赛题若之后公布，早晨决策和晚上记忆可以留着，只换白天那一次感知。
      </p>

      <Link to="/" className="inline-block mt-5 text-sm text-accent">回到今天 →</Link>
    </div>
  )
}
