import os
import os.path as osp
from dataclasses import dataclass, field
from typing import Optional

import rtoml
from mashumaro.mixins.toml import DataClassTOMLMixin

CONFIG_DIR = "config"
if not osp.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)


@dataclass
class Config(DataClassTOMLMixin):
    local_dir: Optional[str] = field(default=None)
    ydnote_dir: Optional[str] = field(default=None)
    smms_secret_token: Optional[str] = field(default=None)
    is_relative_path: bool = field(default=True)


CONFIG_FILE = osp.join(CONFIG_DIR, "config.toml")
if not osp.exists(CONFIG_FILE):
    content = {}
else:
    with open(CONFIG_FILE, encoding="utf-8") as fp:
        content = rtoml.load(fp)
CONFIG = Config.from_dict(content)
