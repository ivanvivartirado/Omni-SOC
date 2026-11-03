import * as echarts from 'echarts/core'
import { BarChart, GaugeChart, HeatmapChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, LineChart, GaugeChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, CanvasRenderer])

export { echarts }

export const baseAxis = {
  axisLine: { lineStyle: { color: '#1e2a44' } },
  axisLabel: { color: '#7c8db5', fontSize: 11 },
  splitLine: { lineStyle: { color: '#1e2a44' } },
}

export const tooltip = { backgroundColor: '#0b1120', borderColor: '#1e2a44', textStyle: { color: '#e2e8f0' } }
