export interface VoiceProcessResponse {
  transcript: string
  responseText: string
  audioStream: ReadableStream<Uint8Array>
}

export class WhisperService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  async processVoice(
    audioBlob: Blob,
    voice: string = 'af_bella'
  ): Promise<VoiceProcessResponse> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.wav')
    formData.append('voice', voice)

    const response = await fetch(`http://${this.baseUrl}/v1/audio/process`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Voice processing failed: ${response.status} - ${error}`)
    }

    const transcript = response.headers.get('X-Transcript') || ''
    const responseText = response.headers.get('X-Response-Text') || ''

    if (!response.body) {
      throw new Error('No audio stream in response')
    }

    return {
      transcript,
      responseText,
      audioStream: response.body
    }
  }
}
