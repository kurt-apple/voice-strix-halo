import { ref, onUnmounted } from 'vue'

export interface MicrophoneState {
  isActive: boolean
  audioContext: AudioContext | null
  mediaStream: MediaStream | null
  analyser: AnalyserNode | null
}

export function useMicrophone() {
  const isActive = ref(false)
  const audioContext = ref<AudioContext | null>(null)
  const mediaStream = ref<MediaStream | null>(null)
  const analyser = ref<AnalyserNode | null>(null)
  const error = ref<string | null>(null)

  async function start(): Promise<boolean> {
    try {
      error.value = null

      // Check if running in a browser context with mediaDevices support
      if (typeof navigator === 'undefined' || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        error.value = 'Microphone access is not supported. Make sure you are using HTTPS or localhost.'
        return false
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })
      
      mediaStream.value = stream
      
      const ctx = new AudioContext({ sampleRate: 16000 })
      audioContext.value = ctx
      
      const source = ctx.createMediaStreamSource(stream)
      const analyserNode = ctx.createAnalyser()
      analyserNode.fftSize = 512
      analyserNode.smoothingTimeConstant = 0.8
      source.connect(analyserNode)
      
      analyser.value = analyserNode
      isActive.value = true
      
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start microphone'
      return false
    }
  }

  function stop() {
    if (mediaStream.value) {
      mediaStream.value.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      mediaStream.value = null
    }
    
    if (audioContext.value) {
      audioContext.value.close()
      audioContext.value = null
    }
    
    analyser.value = null
    isActive.value = false
  }

  function getAudioData(): Float32Array | null {
    if (!analyser.value) return null
    
    const data = new Float32Array(analyser.value.fftSize)
    analyser.value.getFloatTimeDomainData(data)
    return data
  }

  function getAnalyser(): AnalyserNode | null {
    return analyser.value
  }

  onUnmounted(() => {
    stop()
  })

  return {
    isActive,
    error,
    start,
    stop,
    getAudioData,
    getAnalyser,
  }
}
