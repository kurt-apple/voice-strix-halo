<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMicrophone } from '../composables/useMicrophone'
import { WhisperService } from '../services/whisper'
import { PipelineService } from '../services/pipeline'

const serverUrl = ref('localhost:10300')
const pipelineUrl = ref('localhost:10501')
const whisperUrl = computed(() => serverUrl.value)
const pipelineBaseUrl = computed(() => `http://${pipelineUrl.value}`)

const voices = PipelineService.getVoices()
const selectedVoice = ref('af_bella')

const { isActive: micActive, start: startMic, stop: stopMic, getAudioData, error: micError } = useMicrophone()

const transcript = ref('')
const responseText = ref('')
const isProcessing = ref(false)
const error = ref<string | null>(null)
const audioPlayer = ref<HTMLAudioElement | null>(null)
const isRecording = ref(false)
const audioLevel = ref(0)

let whisperService: WhisperService | null = null
let pipelineService: PipelineService | null = null
let audioChunks: Float32Array[] = []
let recordingInterval: number | null = null

function startRecording() {
  if (isRecording.value) return
  
  error.value = null
  transcript.value = ''
  responseText.value = ''
  audioChunks = []

  startMic().then(success => {
    if (!success) {
      error.value = micError.value || 'Failed to start microphone'
      return
    }
    
function calculateAudioLevel(data: Float32Array): number {
  let sum = 0
  for (let i = 0; i < data.length; i++) {
    sum += data[i] * data[i]
  }
  const rms = Math.sqrt(sum / data.length)
  return Math.min(1, rms * 10)
}
    
isRecording.value = true

recordingInterval = window.setInterval(() => {
  const audioData = getAudioData()
  if (audioData) {
    audioChunks.push(new Float32Array(audioData))
    audioLevel.value = calculateAudioLevel(audioData)
  }
}, 100)
  })
}

function stopRecording() {
  if (!isRecording.value) return

  if (recordingInterval) {
    clearInterval(recordingInterval)
    recordingInterval = null
  }

  isRecording.value = false
  audioLevel.value = 0
  stopMic()
  
  processAudio()
}

async function processAudio() {
  if (audioChunks.length === 0) return

  const combined = new Float32Array(audioChunks.length * 1600)
  let offset = 0
  for (const chunk of audioChunks) {
    combined.set(chunk, offset)
    offset += chunk.length
  }
  audioChunks = []

  const pcm16 = floatTo16BitPCM(combined)
  const wavBuffer = createWavFile(pcm16, 16000)
  const audioBlob = new Blob([wavBuffer], { type: 'audio/wav' })

  if (!whisperService) {
    whisperService = new WhisperService(whisperUrl.value)
  }

  isProcessing.value = true
  error.value = null

  try {
    let result
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        result = await whisperService.transcribe(audioBlob)
        break
      } catch (e) {
        if (attempt === 3) throw e
        await new Promise(r => setTimeout(r, 500))
      }
    }
    transcript.value = result.text

    if (result.text.trim()) {
      pipelineService = new PipelineService(pipelineBaseUrl.value, 'qwen3-next', selectedVoice.value)

      isProcessing.value = false
      isProcessing.value = true

      const { response } = await pipelineService.chat([
        { role: 'user', content: result.text }
      ])

      responseText.value = response

      await pipelineService.speechStream(response)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Processing failed'
  } finally {
    isProcessing.value = false
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.code === 'Space' && !e.repeat && !isProcessing.value) {
    e.preventDefault()
    startRecording()
  }
}

function handleKeyUp(e: KeyboardEvent) {
  if (e.code === 'Space') {
    e.preventDefault()
    stopRecording()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
  
  if (recordingInterval) {
    clearInterval(recordingInterval)
  }
  if (micActive.value) {
    stopMic()
  }
})

function floatTo16BitPCM(float32Array: Float32Array): Int16Array {
  const int16Array = new Int16Array(float32Array.length)
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return int16Array
}

function createWavFile(pcmData: Int16Array, sampleRate: number): ArrayBuffer {
  const numChannels = 1
  const bitsPerSample = 16
  const bytesPerSample = bitsPerSample / 8
  const blockAlign = numChannels * bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = pcmData.length * bytesPerSample
  const bufferSize = 44 + dataSize

  const buffer = new ArrayBuffer(bufferSize)
  const view = new DataView(buffer)

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, bufferSize - 8, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, bitsPerSample, true)
  writeString(36, 'data')
  view.setUint32(40, dataSize, true)

  const offset = 44
  for (let i = 0; i < pcmData.length; i++) {
    view.setInt16(offset + i * 2, pcmData[i], true)
  }

  return buffer
}
</script>

<template>
  <div class="voice-pipeline">
    <h1>Voice Pipeline</h1>

    <div class="config">
      <div class="field">
        <label>Whisper Server</label>
        <input v-model="serverUrl" type="text" placeholder="localhost:10300" />
      </div>
      <div class="field">
        <label>Pipeline Server</label>
        <input v-model="pipelineUrl" type="text" placeholder="localhost:10501" />
      </div>
      <div class="field">
        <label>Voice</label>
        <select v-model="selectedVoice">
          <option v-for="voice in voices" :key="voice" :value="voice">{{ voice }}</option>
        </select>
      </div>
    </div>

    <div 
      class="mic-button"
      :class="{ recording: isRecording, processing: isProcessing }"
    >
      <span v-if="isProcessing">Processing...</span>
      <span v-else-if="isRecording">Release to send</span>
      <span v-else>Hold SPACE to talk</span>
      <div v-if="isRecording" class="audio-level">
        <div class="audio-level-bar" :style="{ width: (audioLevel * 100) + '%' }"></div>
      </div>
    </div>

    <div class="hint">
      Press and hold the <strong>space bar</strong> to record your voice
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div class="results">
      <div class="result">
        <label>Transcript</label>
        <div class="text">{{ transcript || 'Your speech will appear here' }}</div>
      </div>

      <div class="result">
        <label>Response</label>
        <div class="text">{{ responseText || 'AI response will appear here' }}</div>
      </div>
    </div>

    <audio ref="audioPlayer" class="audio-player" controls></audio>
  </div>
</template>

<style scoped>
.voice-pipeline {
  background: #16213e;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

h1 {
  text-align: center;
  margin-bottom: 24px;
  font-size: 1.5rem;
  color: #e94560;
}

.config {
  margin-bottom: 24px;
}

.field {
  flex: 1;
}

.field label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.875rem;
  color: #888;
}

.field input {
  width: 100%;
  padding: 12px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1a1a2e;
  color: #eee;
  font-size: 1rem;
}

.field input:focus {
  outline: none;
  border-color: #e94560;
}

.field select {
  width: 100%;
  padding: 12px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1a1a2e;
  color: #eee;
  font-size: 1rem;
  cursor: pointer;
}

.field select:focus {
  outline: none;
  border-color: #e94560;
}

.mic-button {
  width: 100%;
  padding: 40px 20px;
  border: 3px solid #333;
  border-radius: 12px;
  background: #0f3460;
  color: #eee;
  font-size: 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
  user-select: none;
}

.mic-button.recording {
  border-color: #ff4444;
  background: #441111;
  animation: pulse 1s infinite;
}

.mic-button.processing {
  border-color: #f39c12;
  background: #443311;
  cursor: not-allowed;
}

.audio-level {
  width: 100%;
  height: 8px;
  background: #333;
  border-radius: 4px;
  margin-top: 12px;
  overflow: hidden;
}

.audio-level-bar {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #ffeb3b, #ff4444);
  transition: width 0.1s ease-out;
  border-radius: 4px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.hint {
  text-align: center;
  color: #666;
  margin-bottom: 24px;
}

.hint strong {
  color: #e94560;
}

.error {
  padding: 12px;
  background: #ff4444;
  border-radius: 8px;
  margin-bottom: 16px;
  color: white;
}

.results {
  margin-bottom: 24px;
}

.result {
  margin-bottom: 16px;
}

.result label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.875rem;
  color: #888;
}

.result .text {
  padding: 12px;
  background: #1a1a2e;
  border-radius: 8px;
  min-height: 48px;
  color: #eee;
  white-space: pre-wrap;
}

.audio-player {
  width: 100%;
}
</style>