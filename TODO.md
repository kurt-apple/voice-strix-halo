# TODO - Project Shortcomings & Issues

## Known Issues

### voxtral (STT) - NOT WORKING
- **Issue**: Marked as "Not working yet" in documentation
- **Location**: `archive/voxtral/` directory
- **Details**: Uses vLLM with ROCm but has compatibility issues
- **Port**: 10301 (defined but not functional)

## Architecture Issues

### 1. No Continuous Voice Mode
- **Issue**: User must manually hold space bar to record
- **Impact**: No wake word detection, no continuous conversation
- **Frontend**: `frontend/src/components/VoicePipeline.vue:121-133`

### 2. (FIXED) Hardcoded Voice in Frontend
- **Status**: FIXED - Added voice selection dropdown in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`, `frontend/src/services/pipeline.ts`

### 3. Single Conversation Context
- **Issue**: All users share one global conversation context
- **Location**: `voice-pipeline/src/index.ts:22`
- **Impact**: No multi-user support, conversations may confuse between users

### 4. (FIXED) No Streaming Audio
- **Status**: FIXED - Implemented streaming TTS via Kokoro /v1/audio/speech/stream
- **Location**: `voice-pipeline/src/index.ts`, `frontend/src/services/pipeline.ts`, `frontend/src/components/VoicePipeline.vue`

### 5. Context Management is Primitive
- **Issue**: Simple token estimation (chars/4), no real token counting
- **Location**: `voice-pipeline/src/index.ts:48-55`
- **Impact**: May exceed context limits or trim prematurely

## Missing Features

### 6. (FIXED) Wake Word / Porcupine
- **Status**: FIXED - Removed Porcupine dependency, using PTT instead
- **Location**: `frontend/package.json`

### 7. (FIXED) No Voice Configuration UI
- **Status**: FIXED - Added voice selection dropdown in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`

### 8. (FIXED) Hardcoded Server URLs
- **Status**: FIXED - Added separate pipeline URL field in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`

### 9. (FIXED) Audio Level Visualization
- **Status**: FIXED - Added audio level bar in mic button during recording
- **Location**: `frontend/src/components/VoicePipeline.vue`

### 10. (FIXED) Error Recovery
- **Status**: FIXED - Added 3 retries with 500ms delay in frontend
- **Location**: `frontend/src/components/VoicePipeline.vue`

### 19. (FIXED) Input Validation
- **Status**: FIXED - Added validation for messages array, content length, input text length
- **Location**: `voice-pipeline/src/index.ts`

### 11. (FIXED) External Kokoro Dependency
- **Status**: FIXED - Commented out wyoming-kokoro-tts, using local kokoro service instead
- **Location**: `docker-compose.yml`

### 12. (FIXED) Unused TTS Services
- **Status**: FIXED - Commented out Qwen, Chatterbox, Pocket with notes
- **Location**: `docker-compose.yml`

### 14. Fixed Sample Rate
- **Status**: WONTFIX - Whisper expects 16kHz input, forcing 16kHz is correct
- **Location**: `frontend/src/composables/useMicrophone.ts:23`

### 15. No GPU Memory Management
- **Issue**: Services compete for GPU memory without coordination
- **Impact**: May cause OOM errors when running multiple services

### 16. Large Image Sizes
- **Issue**: Multi-arch Docker images are ~20GB
- **Impact**: Long build times, high disk usage

## Code Quality

### 17. No Type Safety in Pipeline Response
- **Issue**: Audio returned as base64 in JSON instead of proper multipart
- **Location**: `voice-pipeline/src/index.ts:202-211`

### 18. Import Order
- **Issue**: `computed` imported after use in VoicePipeline.vue
- **Location**: `frontend/src/components/VoicePipeline.vue:7-10`

### 19. No Input Validation
- **Issue**: No validation on API requests in voice-pipeline
- **Location**: `voice-pipeline/src/index.ts`

### 20. Debug Flags Left On
- **Issue**: Many services default `DEBUG=true`
- **Location**: Multiple services in docker-compose.yml

## Testing/Git Ignore Issues

### 21. .gitignore Too Aggressive
- **Issue**: Data directories not tracked but no way to initialize them
- **Impact**: First run may fail if directories don't exist

## Code Cleanup

### Archived Unused Services
- **Status**: DONE - Moved moonshine, voxtral, piper, qwen3-tts, chatterbox-turbo, pocket-tts to `archive/`
- **Location**: `archive/` directory

## Future Improvements (Not Implemented)

1. Add wake word detection with Porcupine
2. Implement continuous voice conversation mode
3. Add multi-user conversation isolation
4. Stream TTS audio chunks to client
5. Add voice selection UI
6. Add audio level visualization
7. Implement proper token counting for context management
8. Add service health checks that verify GPU availability
9. Add automatic GPU memory management
10. Implement conversation history persistence
