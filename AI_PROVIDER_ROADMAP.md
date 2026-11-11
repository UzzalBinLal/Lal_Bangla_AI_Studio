# Lal Bangla AI Video Studio — free-first roadmap

## Available in the free-first build
- Bengali male/female voice generation through the existing Edge TTS server route.
- Existing-video voiceover rendering with FFmpeg and subtitle track.
- Photo presenter MP4: selected still image + Bengali speech + timed captions.
- News presenter MP4: user-selected presenter image + Bengali news script + speech + captions.
- News presenter photo is stored locally in the user's browser IndexedDB on that device.
- PWA install metadata and service-worker caching.

## Important current limitation
The photo presenter and news presenter routes currently create a still-image video with speech and captions. They do **not** animate the face or synchronize the lips. The interface says this explicitly. Do not advertise these free routes as realistic talking-photo/lip-sync generation.

## Optional future AI provider
The backend can later add a provider adapter (for example, HeyGen Avatar IV) behind the same photo/news UI. Configure secrets only in the hosting provider's environment settings:
- `AI_VIDEO_PROVIDER=heygen`
- `HEYGEN_API_KEY`

Do not put API keys in browser JavaScript, HTML, Git history, or public environment files. Before enabling a paid provider, confirm account plan, API access, current pricing, consent/identity requirements, retention policy, and commercial rights.

## Hosting requirements
- Python dependencies from `requirements.txt`
- FFmpeg and FFprobe installed on the server
- Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- HTTPS is required for installable PWA features and future Play Store Trusted Web Activity verification.
- The free photo/news endpoint is CPU/FFmpeg rendering; long scripts and high-resolution uploads may exceed free-host CPU/RAM/time limits.

## Android / Play Store
The existing web app can be packaged as a Trusted Web Activity after the production domain is stable. This still requires a signed Android App Bundle, Play Console developer account, Digital Asset Links at `/.well-known/assetlinks.json`, privacy policy, store listing, and review. A website deployment alone does not publish an app to Play Store.
