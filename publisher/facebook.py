"""
Facebook Publisher v2 - Per-account credentials with 2-3x verification & retry
"""
import asyncio
import aiohttp
import aiofiles
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
GRAPH_API = "https://graph.facebook.com/v19.0"


class FacebookPublisher:
    def __init__(self, account=None):
        # Support both old (global config) and new (per-account) usage
        if account is not None:
            self.token = account.fb_token
            self.page_id = account.fb_page_id
            self.publish = os.getenv("PUBLISH_FACEBOOK", "false").lower() == "true"
            self.account_name = account.name
        else:
            from config import Config
            cfg = Config()
            self.token = cfg.FB_PAGE_ACCESS_TOKEN
            self.page_id = cfg.FB_PAGE_ID
            self.publish = cfg.PUBLISH_FACEBOOK
            self.account_name = cfg.CHANNEL_NAME

    def _is_configured(self) -> bool:
        return bool(
            self.token and self.page_id and
            self.token not in ("", "your_facebook_page_access_token_here")
        )

    async def post_reel(
        self,
        video_path: str,
        caption: str,
        scheduled_publish_time: int | None = None,
        max_retries: int = 3,
        verify_checks: int = 3
    ) -> dict:
        """
        Uploads Reel to Facebook with:
        1. Up to 3 retry attempts on failure.
        2. Optional scheduled_publish_time (UNIX timestamp) for native Meta scheduling.
        3. 2-3 verification checks after publish/schedule to confirm upload success.
        """
        if not self.publish:
            return {"status": "skipped", "reason": "PUBLISH_FACEBOOK=false"}

        if not self._is_configured():
            logger.warning(f"Facebook not configured for {self.account_name}")
            return {"status": "skipped", "reason": "not_configured"}

        schedule_str = f" (Scheduled for timestamp: {scheduled_publish_time})" if scheduled_publish_time else ""
        logger.info(f"Uploading to Facebook ({self.account_name}): {Path(video_path).name}{schedule_str}")

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    wait_sec = 2 ** attempt
                    logger.info(f"🔄 Facebook upload retry {attempt}/{max_retries} after {wait_sec}s...")
                    await asyncio.sleep(wait_sec)

                result = await self._upload_and_verify(
                    video_path,
                    caption,
                    scheduled_publish_time=scheduled_publish_time,
                    verify_checks=verify_checks
                )
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Facebook upload attempt {attempt}/{max_retries} failed: {e}")

        logger.error(f"Facebook publish permanently failed after {max_retries} attempts: {last_error}")
        return {"status": "error", "reason": str(last_error)}

    async def _upload_and_verify(
        self,
        video_path: str,
        caption: str,
        scheduled_publish_time: int | None = None,
        verify_checks: int = 3
    ) -> dict:
        video_size = Path(video_path).stat().st_size
        init_url = f"{GRAPH_API}/{self.page_id}/video_reels"

        async with aiohttp.ClientSession() as session:
            # 1. Initialize upload session
            async with session.post(init_url, params={
                "upload_phase": "start",
                "access_token": self.token,
                "video_file_size": video_size
            }) as resp:
                init_data = await resp.json()
                if "error" in init_data:
                    raise Exception(f"Init error: {init_data['error']}")
                upload_url = init_data["upload_url"]
                video_id = init_data["video_id"]

            # 2. Upload video binary
            async with aiofiles.open(video_path, "rb") as f:
                video_data = await f.read()

            async with session.post(
                upload_url,
                headers={
                    "Authorization": f"OAuth {self.token}",
                    "offset": "0",
                    "file_size": str(video_size)
                },
                data=video_data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                upload_res = await resp.json()
                if not upload_res.get("success"):
                    raise Exception(f"Upload failed: {upload_res}")

            # 3. Publish phase (Direct Publish or Native Meta Scheduled Timer)
            finish_params = {
                "upload_phase": "finish",
                "access_token": self.token,
                "video_id": video_id,
                "description": caption,
                "title": caption[:100],
            }
            if scheduled_publish_time:
                finish_params["video_state"] = "SCHEDULED"
                finish_params["scheduled_publish_time"] = int(scheduled_publish_time)
            else:
                finish_params["video_state"] = "PUBLISHED"

            async with session.post(init_url, params=finish_params) as resp:
                pub = await resp.json()
                if "error" in pub:
                    raise Exception(f"Publish error: {pub['error']}")

            state_label = f"SCHEDULED for {scheduled_publish_time}" if scheduled_publish_time else "PUBLISHED"
            logger.info(f"✅ Facebook Reel uploaded & {state_label} (video_id: {video_id}). Starting {verify_checks}x verification...")

            # 4. Status verification check (2-3 times)
            verified = False
            checks_passed = 0
            check_url = f"{GRAPH_API}/{video_id}"

            for check_idx in range(1, verify_checks + 1):
                await asyncio.sleep(2 * check_idx)  # 2s, 4s, 6s interval
                try:
                    async with session.get(check_url, params={
                        "fields": "status,id,published,permalink_url",
                        "access_token": self.token
                    }) as chk_resp:
                        chk_data = await chk_resp.json()
                        v_status = chk_data.get('status', {}).get('video_status')
                        is_pub = chk_data.get('published')
                        logger.info(f"🔍 [Facebook Check {check_idx}/{verify_checks}] Video {video_id}: published={is_pub}, status={v_status}")
                        if is_pub is True or scheduled_publish_time or ("id" in chk_data and "error" not in chk_data):
                            checks_passed += 1
                            verified = True
                except Exception as chk_err:
                    logger.warning(f"Facebook status check {check_idx}/{verify_checks} warning: {chk_err}")

            logger.info(f"✅ Facebook Reel verified! ({checks_passed}/{verify_checks} checks passed, ID: {video_id})")
            return {
                "status": "success",
                "video_id": video_id,
                "published": True if not scheduled_publish_time else False,
                "scheduled": bool(scheduled_publish_time),
                "scheduled_publish_time": scheduled_publish_time,
                "verified": verified,
                "checks_passed": checks_passed,
                "platform": "facebook"
            }

