import axios from 'axios'

export interface WhisperResponse {
  text: string
}

export class WhisperService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  async transcribe(audioBlob: Blob): Promise<WhisperResponse> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.wav')

    const response = await axios.post<WhisperResponse>(
      `${this.baseUrl}/transcribe`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return response.data
  }
}