import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { SecEvent } from './types'

interface LiveCtx {
  events: SecEvent[]
  connected: boolean
  lastCritical: SecEvent | null
  sound: boolean
  setSound: (v: boolean) => void
}

const MAX = 200
const Ctx = createContext<LiveCtx>({ events: [], connected: false, lastCritical: null, sound: false, setSound: () => {} })

function beep() {
  try {
    const ac = new AudioContext()
    const o = ac.createOscillator()
    const g = ac.createGain()
    o.type = 'square'
    o.frequency.value = 880
    g.gain.value = 0.05
    o.connect(g).connect(ac.destination)
    o.start()
    o.stop(ac.currentTime + 0.25)
  } catch {
    /* sin audio */
  }
}

export function LiveProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [events, setEvents] = useState<SecEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [lastCritical, setLastCritical] = useState<SecEvent | null>(null)
  const [sound, setSoundState] = useState(() => localStorage.getItem('soc:sound') === '1')
  const soundRef = useRef(sound)
  soundRef.current = sound

  useEffect(() => {
    let ws: WebSocket | null = null
    let retry = 1000
    let timer: ReturnType<typeof setTimeout> | undefined
    let invalidateTimer: ReturnType<typeof setTimeout> | undefined
    let stopped = false

    const connect = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/api/ws/events`)
      ws.onopen = () => {
        setConnected(true)
        retry = 1000
      }
      ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data)
        if (data.type !== 'event') return
        const ev = data.data as SecEvent
        setEvents((prev) => [ev, ...prev].slice(0, MAX))
        if (ev.severity >= 4) {
          setLastCritical(ev)
          if (soundRef.current) beep()
        }
        invalidateTimer ??= setTimeout(() => {
          invalidateTimer = undefined
          qc.invalidateQueries({ queryKey: ['summary'] })
        }, 5000)
      }
      ws.onclose = () => {
        setConnected(false)
        if (stopped) return
        timer = setTimeout(connect, retry)
        retry = Math.min(retry * 2, 30000)
      }
    }
    connect()
    return () => {
      stopped = true
      clearTimeout(timer)
      clearTimeout(invalidateTimer)
      ws?.close()
    }
  }, [qc])

  const setSound = (v: boolean) => {
    localStorage.setItem('soc:sound', v ? '1' : '0')
    setSoundState(v)
  }

  return <Ctx.Provider value={{ events, connected, lastCritical, sound, setSound }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useLive = () => useContext(Ctx)
