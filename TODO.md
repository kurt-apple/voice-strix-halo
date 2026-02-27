# TODO - Current Issues & Improvements

## Critical Issues

### 1. Frontend Does Orchestration (Architecture Issue)
- **Issue**: Frontend manages the full pipeline: mic → Whisper → orchestrator → audio playback
- **Current Flow**: Frontend → Whisper → Frontend → Orchestrator → Frontend
- **Desired Flow**: Frontend → Whisper → Orchestrator → Frontend
- **Location**: `frontend/src/components/VoicePipeline.vue:80-134`
- **Impact**: Orchestrator doesn't actually orchestrate - frontend does
- **Fix Needed**: Whisper should forward transcripts to orchestrator, orchestrator returns audio

## Architecture Issues

### 2. No Continuous Voice Mode
- **Issue**: User must manually hold space bar to record
- **Impact**: No wake word detection, no continuous conversation
- **Location**: `frontend/src/components/VoicePipeline.vue:136-148`

### 3. Single Conversation Context
- **Issue**: All users share one global conversation context
- **Location**: `orchestrator/src/index.ts:22`
- **Impact**: No multi-user support, conversations may confuse between users

### 4. Context Management is Primitive
- **Issue**: Simple token estimation (chars/4), no real token counting
- **Location**: `orchestrator/src/index.ts:48-55`
- **Impact**: May exceed context limits or trim prematurely

### 5. No GPU Memory Management
- **Issue**: Services compete for GPU memory without coordination
- **Impact**: May cause OOM errors when running multiple services

### 6. Large Docker Image Sizes
- **Issue**: Multi-arch Docker images are ~20GB
- **Impact**: Long build times, high disk usage

## Code Quality Issues

### 7. Base64 Audio in JSON
- **Issue**: Audio returned as base64 in JSON instead of proper streaming/multipart
- **Location**: `orchestrator/src/index.ts:267-280`
- **Impact**: Less efficient than streaming binary data (though streaming is also implemented)

### 8. .gitignore Too Aggressive
- **Issue**: Data directories not tracked but no way to initialize them
- **Impact**: First run may fail if directories don't exist

## Future Improvements

1. Implement continuous voice conversation mode with wake word detection
2. Add multi-user conversation isolation (session IDs)
3. Implement proper token counting for context management (use tiktoken or similar)
4. Add service health checks that verify GPU availability
5. Add automatic GPU memory management
6. Implement conversation history persistence (database or file-based)
7. Add conversation reset/clear endpoint
8. Stream LLM responses (not just TTS)

## Research Questions

- Can Kokoro stream audio output from a streamed text input, to reduce latency?
- Should we implement proper multipart responses instead of base64 JSON?
- What's the best way to handle session management for multi-user support?
