# Lal Bangla AI Video Studio

A Bengali-first, mobile-friendly video studio with a free-first workflow.

## Free features
- Bengali text-to-speech MP3 (female and male voices) using the existing Edge TTS route.
- Add Bengali voiceover and captions to a selected video; export MP4.
- Photo presenter: selected portrait + Bengali speech + timed captions; export MP4.
- News presenter: save a chosen presenter photo locally in the browser (IndexedDB), enter news text, generate Bengali narration and captions, export MP4.
- Installable PWA metadata and service-worker cache.

**Honest limitation:** free photo/news exports currently keep the portrait still. They do not animate facial movement or synchronize lips. Realistic talking-photo lip-sync is reserved for a later optional AI model/provider integration.

## Run locally
Python 3.10+ and FFmpeg/FFprobe are required.

```bash
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000`.

## Deploy
Configure the hosting service to install Python requirements and run:

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

Install FFmpeg and FFprobe in the hosting environment. The app uses the same-origin API routes. For production, use HTTPS, upload limits, rate limiting, and a privacy policy.

## Future paid AI
See [AI_PROVIDER_ROADMAP.md](AI_PROVIDER_ROADMAP.md). Optional provider credentials must be stored as server environment variables only. Never expose API keys in browser HTML or JavaScript.

## Android / Play Store
The PWA can later be packaged as an Android Trusted Web Activity after the production domain is stable and Digital Asset Links, signed Android App Bundle, Play Console listing, privacy disclosures, and review are completed.
