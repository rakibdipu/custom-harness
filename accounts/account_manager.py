"""
Account Manager - Loads and manages all accounts from JSON configs
Each account = one Facebook Page + one YouTube Channel + its own content style
"""
import json
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Represents one social media account/channel"""
    id: str
    name: str
    tagline: str
    niche: str
    content_types: list
    schedule: dict
    visual_style: str
    subtitle_style: str
    bgm_style: str
    tts_voice: str
    tts_rate: str
    color_primary: str
    color_bg: str
    color_text: str
    long_video_duration_min: int
    facebook: dict
    youtube: dict
    enabled: bool
    auto_reel_from_long: bool

    @property
    def fb_page_id(self) -> str:
        env_key = self.facebook.get("page_id_env", "")
        return os.getenv(env_key, "")

    @property
    def fb_token(self) -> str:
        env_key = self.facebook.get("token_env", "")
        return os.getenv(env_key, "")

    @property
    def yt_credentials_file(self) -> str:
        return self.youtube.get("credentials_file", "")

    @property
    def yt_client_secrets(self) -> str:
        return self.youtube.get("client_secrets", "")

    @property
    def is_fb_configured(self) -> bool:
        return bool(self.fb_page_id and self.fb_token)

    @property
    def is_yt_configured(self) -> bool:
        return Path(self.yt_client_secrets).exists()


class AccountManager:
    def __init__(self, accounts_dir: str = "accounts"):
        self.accounts_dir = Path(accounts_dir)
        self._accounts: dict[str, Account] = {}
        self._load_all()

    def _load_all(self):
        """Load all JSON account configs"""
        json_files = list(self.accounts_dir.glob("*.json"))
        if not json_files:
            logger.warning(f"No account configs found in {self.accounts_dir}")
            return

        for path in json_files:
            if path.name.endswith("_plan.json"):
                continue
            try:
                with open(path) as f:
                    data = json.load(f)
                account = Account(**data)
                self._accounts[account.id] = account
                status = "✅" if account.enabled else "⏸️"
                logger.info(f"{status} Account loaded: [{account.id}] {account.name} | {account.niche}")
            except Exception as e:
                logger.error(f"Failed to load account {path.name}: {e}")

    def get_all(self, enabled_only: bool = True) -> list[Account]:
        accounts = list(self._accounts.values())
        if enabled_only:
            accounts = [a for a in accounts if a.enabled]
        return accounts

    def get(self, account_id: str) -> Optional[Account]:
        return self._accounts.get(account_id)

    def list_ids(self) -> list[str]:
        return list(self._accounts.keys())

    def enable(self, account_id: str):
        if account_id in self._accounts:
            self._accounts[account_id].enabled = True
            self._save(account_id)

    def disable(self, account_id: str):
        if account_id in self._accounts:
            self._accounts[account_id].enabled = False
            self._save(account_id)

    def _save(self, account_id: str):
        """Save account config back to JSON"""
        account = self._accounts[account_id]
        path = self.accounts_dir / f"{account_id}.json"
        with open(path, "w") as f:
            import dataclasses
            json.dump(dataclasses.asdict(account), f, indent=2)
