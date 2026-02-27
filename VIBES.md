# VIBES - Completed Improvements

This file tracks features and issues that have been successfully implemented and resolved.

## Completed Features

### 2. Voice Configuration
- **Completed**: Added voice selection dropdown in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`, `frontend/src/services/pipeline.ts`
- **Impact**: Users can now select different TTS voices from the UI

### 4. Streaming Audio
- **Completed**: Implemented streaming TTS via Kokoro /v1/audio/speech/stream
- **Location**: `voice-pipeline/src/index.ts`, `frontend/src/services/pipeline.ts`, `frontend/src/components/VoicePipeline.vue`
- **Impact**: Audio plays as it's generated, reducing perceived latency

### 6. Wake Word / Porcupine
- **Completed**: Removed Porcupine dependency, using Push-to-Talk instead
- **Location**: `frontend/package.json`
- **Rationale**: PTT is simpler and more reliable for this use case

### 7. Voice Configuration UI
- **Completed**: Added voice selection dropdown in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`
- **Impact**: Easy voice switching without config file changes

### 8. Server URL Configuration
- **Completed**: Added separate pipeline URL field in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`
- **Impact**: Users can point to different backend instances

### 9. Audio Level Visualization
- **Completed**: Added audio level bar in mic button during recording
- **Location**: `frontend/src/components/VoicePipeline.vue`
- **Impact**: Visual feedback shows recording is active and picking up audio

### 10. Error Recovery
- **Completed**: Added 3 retries with 500ms delay in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`
- **Impact**: Transient network errors don't immediately fail requests

### 11. External Kokoro Dependency
- **Completed**: Using local kokoro service instead of external API
- **Location**: `docker-compose.yml`
- **Impact**: Self-contained deployment, no external dependencies

### 12. Unused TTS Services
- **Completed**: Commented out Qwen, Chatterbox, Pocket with notes
- **Location**: `docker-compose.yml`
- **Impact**: Cleaner config, focused on working services

### 14. Fixed Sample Rate (WONTFIX)
- **Status**: Correctly forcing 16kHz - Whisper expects this input
- **Location**: `frontend/src/composables/useMicrophone.ts:23`
- **Rationale**: Not a bug, this is the correct implementation

### 19. Input Validation
- **Completed**: Added validation for messages array, content length, input text length
- **Location**: `voice-pipeline/src/index.ts`
- **Impact**: Better error messages, prevents crashes from malformed requests

## Code Cleanup Completed

### Archived Unused Services
- **Completed**: Moved moonshine, voxtral, piper, qwen3-tts, chatterbox-turbo, pocket-tts to `archive/`
- **Location**: `archive/` directory
- **Impact**: Cleaner project structure, easier navigation

### Wyoming Protocol Replaced with REST API
- **Completed**: Replaced wyoming-faster-whisper with custom FastAPI REST server
- **Location**: `whisper/whisper_server.py`, `whisper/Dockerfile`
- **Impact**: Simpler HTTP REST API instead of Wyoming TCP protocol, easier integration
- **Endpoints**: `/transcribe`, `/v1/audio/transcriptions`, `/health`

### Service Renamed to Orchestrator
- **Completed**: Renamed voice-pipeline service to orchestrator for clarity
- **Location**: `orchestrator/` directory (formerly `voice-pipeline/`), `docker-compose.yml`, README.md, TODO.md
- **Impact**: Service name now reflects its role as conversation orchestrator

### Function Scope Fix in Frontend
- **Completed**: Moved `calculateAudioLevel` out of `startRecording` function scope to module level
- **Location**: `frontend/src/components/VoicePipeline.vue`
- **Impact**: Better code organization, function not recreated on every call

### Debug Flags Configuration
- **Completed**: All DEBUG flags in .env.example are already set to false by default
- **Location**: `.env.example`
- **Impact**: Production-safe defaults, verbose logging only when explicitly enabled
