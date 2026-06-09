# Error Reference

| Code | Class | Level | Message | Remediation |
| --- | --- | --- | --- | --- |
| E001 | BBDownNotFoundError | FATAL | BBDown not found | Run `./install.sh` |
| E002 | BBDownAuthError | FATAL | BBDown authentication required | Run `BBDown login` |
| E003 | BBDownDownloadError | RECOVERABLE | Failed to download subtitles | Check URL/network/login/language |
| E004 | NoSubtitleError | RECOVERABLE | No downloadable subtitles | Try another language or video |
| E005 | InvalidURLError | FATAL | Invalid Bilibili URL or ID | Provide a Bilibili URL, BV ID, or av ID |
| E006 | OutputWriteError | FATAL | Cannot write output | Check output permissions |
| E007 | SubtitleContentError | RECOVERABLE | Invalid subtitle content | Retry or inspect BBDown output |
