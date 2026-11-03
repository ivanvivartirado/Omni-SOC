import ReactEChartsCore from 'echarts-for-react/lib/core'
import { baseAxis, echarts, tooltip } from '../lib/echarts'
import { SEV_COLOR, SEV_LABEL, scoreColor } from '../lib/format'
import type { Summary } from '../lib/types'

const Chart = ({ option, height = 260 }: { option: object; height?: number }) => (
  <ReactEChartsCore echarts={echarts} option={option} style={{ height }} notMerge lazyUpdate />
)

export function ScoreGauge({ value }: { value: number | null }) {
  const color = scoreColor(value)
  return (
    <Chart
      height={200}
      option={{
        series: [
          {
            type: 'gauge',
            startAngle: 210,
            endAngle: -30,
            min: 0,
            max: 100,
            progress: { show: true, width: 14, itemStyle: { color } },
            axisLine: { lineStyle: { width: 14, color: [[1, '#1e2a44']] } },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            pointer: { show: false },
            detail: { valueAnimation: true, formatter: value == null ? '—' : '{value}', color, fontSize: 40, offsetCenter: [0, 0] },
            title: { show: true, offsetCenter: [0, '40%'], color: '#7c8db5', fontSize: 12 },
            data: [{ value: value ?? 0, name: 'de 100' }],
          },
        ],
      }}
    />
  )
}

export function Timeline({ data, range }: { data: Summary['charts']['timeline']; range: '24h' | '7d' }) {
  const labels = data.map((d) =>
    new Date(d.bucket).toLocaleString('es-ES', range === '24h' ? { hour: '2-digit', minute: '2-digit' } : { day: '2-digit', month: 'short' }),
  )
  const series = ([1, 2, 3, 4] as const).map((s) => ({
    name: SEV_LABEL[s],
    type: 'bar',
    stack: 'sev',
    itemStyle: { color: SEV_COLOR[s] },
    emphasis: { focus: 'series' },
    data: data.map((d) => d[`s${s}`]),
  }))
  return (
    <Chart
      option={{
        tooltip: { ...tooltip, trigger: 'axis' },
        legend: { textStyle: { color: '#7c8db5' }, top: 0 },
        grid: { left: 40, right: 10, top: 30, bottom: 25 },
        xAxis: { type: 'category', data: labels, ...baseAxis, splitLine: { show: false } },
        yAxis: { type: 'value', ...baseAxis },
        series,
      }}
    />
  )
}

export function HBar({ items, height = 260 }: { items: { label: string; value: number; sev: number }[]; height?: number }) {
  const rev = [...items].reverse()
  return (
    <Chart
      height={height}
      option={{
        tooltip: { ...tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 10, right: 30, top: 5, bottom: 5, containLabel: true },
        xAxis: { type: 'value', ...baseAxis },
        yAxis: {
          type: 'category',
          data: rev.map((i) => i.label),
          ...baseAxis,
          axisLabel: { ...baseAxis.axisLabel, width: 200, overflow: 'truncate' },
        },
        series: [
          {
            type: 'bar',
            data: rev.map((i) => ({ value: i.value, itemStyle: { color: SEV_COLOR[i.sev] } })),
            label: { show: true, position: 'right', color: '#cbd5e1', fontSize: 11 },
          },
        ],
      }}
    />
  )
}

export function Heatmap({ data }: { data: Summary['charts']['heatmap'] }) {
  const points = data.cells
  const max = Math.max(1, ...points.map((c) => c[2]))
  const hours = data.hours.map((h) => new Date(h).toLocaleTimeString('es-ES', { hour: '2-digit' }) + 'h')
  return (
    <Chart
      height={Math.max(160, data.hosts.length * 28 + 60)}
      option={{
        tooltip: { ...tooltip, formatter: (p: { value: [number, number, number] }) => `${data.hosts[p.value[1]]} · ${hours[p.value[0]]}: ${p.value[2]} alertas` },
        grid: { left: 10, right: 10, top: 5, bottom: 45, containLabel: true },
        xAxis: { type: 'category', data: hours, ...baseAxis, splitArea: { show: false } },
        yAxis: { type: 'category', data: data.hosts, ...baseAxis },
        visualMap: {
          min: 0,
          max,
          calculable: false,
          orient: 'horizontal',
          left: 'center',
          bottom: 0,
          itemHeight: 120,
          textStyle: { color: '#7c8db5' },
          inRange: { color: ['#111a2e', '#1e3a5f', '#eab308', '#f97316', '#ef4444'] },
        },
        series: [{ type: 'heatmap', data: points, itemStyle: { borderColor: '#0b1120', borderWidth: 1 } }],
      }}
    />
  )
}
