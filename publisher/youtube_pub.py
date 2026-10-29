"""
YouTube Publisher - Uploads Shorts via YouTube Data API v3
Per-account credentials + account-aware channel metadata with 2-3x verification & retry
"""
import asyncio
import pickle
import logging
import os
import time
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


class YouTubePublisher:
    def __init__(self, account=None):
        self.config = Config()
        self.account = account
        # Per-account credentials (preferred) or fall back to global config
        if account is not None:
            self.cred_file = account.yt_credentials_file or self.config.YT_CREDENTIALS_FILE
            self.client_secrets = account.yt_client_secrets or self.config.YT_CLIENT_SECRETS_FILE
            self.publish = os.getenv("PUBLISH_YOUTUBE", "false").lower() == "true"
            # Use account-specific channel name for description
            self.channel_name = account.name
            self.channel_niche = account.niche
        else:
            self.cred_file = self.config.YT_CREDENTIALS_FILE
            self.client_secrets = self.config.YT_CLIENT_SECRETS_FILE
            self.publish = self.config.PUBLISH_YOUTUBE
            self.channel_name = self.config.CHANNEL_NAME
            self.channel_niche = self.config.NICHE

    def _is_configured(self) -> bool:
        return Path(self.client_secrets).exists()

    def _get_credentials(self):
        """Get or refresh YouTube OAuth credentials"""
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
        creds = None
        cred_file = self.cred_file

        if Path(cred_file).exists():
            with open(cred_file, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(cred_file, "wb") as f:
                pickle.dump(creds, f)

        return creds

    async def upload(self, video_path: str, title: str, description: str, tags: list, max_retries: int = 3, verify_checks: int = 3) -> dict:
        """
        Uploads Short to YouTube with:
        1. Up to 3 retry attempts on transient network errors.
        2. 2-3 verification checks to verify video status on YouTube.
        """
        if not self.publish:
            logger.info("YouTube publishing disabled (PUBLISH_YOUTUBE=false)")
            return {"status": "skipped", "reason": "disabled"}

        if not self._is_configured():
            logger.warning("YouTube not configured — add client_secret.json to project root")
            return {"status": "skipped", "reason": "not_configured"}

        logger.info(f"Uploading to YouTube ({self.channel_name}): {Path(video_path).name}")

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    wait_sec = 2 ** attempt
                    logger.info(f"🔄 YouTube upload retry {attempt}/{max_retries} after {wait_sec}s...")
                    await asyncio.sleep(wait_sec)

                # Run sync upload in thread pool to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_upload_and_verify, video_path, title, description, tags, verify_checks
                )
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"YouTube upload attempt {attempt}/{max_retries} failed: {e}")

        logger.error(f"YouTube upload permanently failed after {max_retries} attempts: {last_error}")
        return {"status": "error", "reason": str(last_error)}

    def _sync_upload_and_verify(self, video_path: str, title: str, description: str, tags: list, verify_checks: int = 3) -> dict:
        """Synchronous YouTube upload + 2-3x status verification check (runs in thread pool)"""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = self._get_credentials()
        youtube = build("youtube", "v3", credentials=creds)

        # Account-aware metadata — uses per-account channel name and niche
        full_description = (
            f"{description}\n\n"
            f"#{self.channel_niche.replace(' ', '')} #Shorts\n\n"
            f"Subscribe to {self.channel_name} for daily {self.channel_niche} content."
        )

        body = {
            "snippet": {
                "title": title[:100],
                "description": full_description[:5000],
                "tags": tags + ["Shorts", self.channel_niche],
                "categoryId": "22",  # People & Blogs
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
                "madeForKids": False
            }
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            chunksize=1024 * 1024 * 5,   # 5MB chunks
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube upload: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        logger.info(f"✅ YouTube Short uploaded! ID: {video_id}. Starting {verify_checks}x verification...")

        # 2-3 verification checks on YouTube
        checks_passed = 0
        verified = False
        for check_idx in range(1, verify_checks + 1):
            time.sleep(2 * check_idx)  # 2s, 4s, 6s
            try:
                chk_req = youtube.videos().list(part="status,snippet", id=video_id)
                chk_res = chk_req.execute()
                items = chk_res.get("items", [])
                if items:
                    v_status = items[0].get("status", {}).get("uploadStatus", "uploaded")
                    logger.info(f"🔍 [YouTube Check {check_idx}/{verify_checks}] Video {video_id} status: {v_status}")
                    checks_passed += 1
                    verified = True
            except Exception as chk_err:
                logger.warning(f"YouTube status check {check_idx}/{verify_checks} error: {chk_err}")

        logger.info(f"✅ YouTube Short verified! ({checks_passed}/{verify_checks} checks passed, ID: {video_id})")
        logger.info(f"URL: https://www.youtube.com/shorts/{video_id}")

        return {
            "status": "success",
            "video_id": video_id,
            "url": f"https://www.youtube.com/shorts/{video_id}",
            "verified": verified,
            "checks_passed": checks_passed,
            "platform": "youtube"
        }
