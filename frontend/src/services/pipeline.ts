import axios from 'axios'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatCompletionRequest {
  model: string
  messages: ChatMessage[]
}

export interface ChatCompletionResponse {
  choices: Array<{
    message: {
      role: string
      content: string
    }
  }>
  audio?: string
  content_type?: string
}

export type AudioChunkCallback = (audioData: Uint8Array) => void

const VOICES = [
  'af_bella', 'af_sarah', 'af_sky',
  'am_adam', 'am_michael',
  'bf_emma', 'bf_isabella',
  'bm_george', 'bm_lewis',
  'onyx', 'nova', 'shimmer'
]

let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  return audioContext
}

async function playWavChunk(wavData: Uint8Array): Promise<void> {
  const ctx = getAudioContext()
  
  try {
    const audioBuffer = await ctx.decodeAudioData(wavData.buffer.slice(0))
    const source = ctx.createBufferSource()
    source.buffer = audioBuffer
    source.connect(ctx.destination)
    source.start()
  } catch (e) {
    console.error('Failed to decode audio chunk:', e)
  }
}

export class PipelineService {
  private baseUrl: string
  private model: string
  private voice: string

  constructor(baseUrl: string, model: string = 'qwen3-next', voice: string = 'af_bella') {
    this.baseUrl = baseUrl.replace(/\/$/, '')
    this.model = model
    this.voice = voice
  }

  static getVoices(): string[] {
    return VOICES
  }

  async chat(messages: ChatMessage[]): Promise<{ response: string; audio?: Uint8Array }> {
    const request: ChatCompletionRequest & { voice?: string } = {
      model: this.model,
      messages,
      voice: this.voice,
    }

    const response = await axios.post<ChatCompletionResponse>(
      `${this.baseUrl}/v1/chat/completions`,
      request,
      {
        responseType: 'json',
      }
    )

    const data = response.data
    const text = data.choices[0]?.message?.content || ''
    
    let audio: Uint8Array | undefined
    if (data.audio) {
      const binary = atob(data.audio)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
      }
      audio = bytes
    }

    return { response: text, audio }
  }

  async speech(text: string): Promise<Uint8Array> {
    const response = await axios.post(
      `${this.baseUrl}/v1/audio/speech`,
      {
        model: 'kokoro',
        input: text,
        voice: this.voice,
        response_format: 'wav',
      },
      {
        responseType: 'arraybuffer',
      }
    )

    return new Uint8Array(response.data)
  }

  async speechStream(text: string, onChunk?: AudioChunkCallback): Promise<void> {
    const response = await fetch(`${this.baseUrl}/v1/audio/speech/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'kokoro',
        input: text,
        voice: this.voice,
        response_format: 'wav',
      }),
    })

    if (!response.ok) {
      throw new Error(`TTS stream failed: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('No response body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = new Uint8Array(0)

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = value
        const newBuffer = new Uint8Array(buffer.length + chunk.length)
        newBuffer.set(buffer)
        newBuffer.set(chunk, buffer.length)
        buffer = newBuffer

        if (onChunk) {
          onChunk(new Uint8Array(chunk))
        }

        await playWavChunk(chunk)
      }
    } finally {
      reader.releaseLock()
    }
  }
}