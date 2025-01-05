import logging
import os
import os.path as osp
import platform
import re
import xml.etree.ElementTree as ET
from enum import Enum, auto
from typing import Optional

from win32_setctime import setctime

from .api import YoudaoNoteSession
from .config import CONFIG
from .convert import YoudaoNoteConvert
from .image import ImagePull

MARKDOWN_SUFFIX = ".md"


class FileType(Enum):
    OTHER = auto()
    MARKDOWN = auto()
    XML = auto()
    JSON = auto()


class FileActionEnum(Enum):
    CONTINUE = auto()
    ADD = auto()
    UPDATE = auto()


SESSION = YoudaoNoteSession()


class YoudaoNotePull:
    def __init__(self):
        local_dir = CONFIG.local_dir or "youdaonote"
        if not osp.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        self.root_local_dir = local_dir

        logging.info("本次使用 Cookies 登录")

        self.smms_secret_token = CONFIG.smms_secret_token or ""
        self.is_relative_path = CONFIG.is_relative_path

    def _get_ydnote_dir_id(self, ydnote_dir: Optional[str]) -> str:
        """
        获取指定有道云笔记指定目录 ID
        :param ydnote_dir: 指定有道云笔记指定目录
        :return: dir_id, error_msg
        """
        root_dir_info = SESSION.get_root_dir_info_id()
        root_dir_id = root_dir_info["fileEntry"]["id"]

        # 如果不指定文件夹，取根目录 ID
        if not ydnote_dir:
            return root_dir_id

        dir_info = SESSION.get_dir_info_by_id(root_dir_id)
        for entry in dir_info["entries"]:
            file_entry = entry["fileEntry"]
            if file_entry["name"] == ydnote_dir:
                return file_entry["id"]

        raise ValueError(f"「有道云笔记」指定目录不存在：{ydnote_dir}")

    def _judge_type(self, file_id, youdao_file_suffix: str) -> FileType:
        """判断笔记类型"""
        # 1、如果文件是 .md 类型
        if youdao_file_suffix == MARKDOWN_SUFFIX:
            return FileType.MARKDOWN
        elif youdao_file_suffix in {".note", ".clip", ""}:
            response = SESSION.get_file_by_id(file_id)
            content = response.content
            # 2、如果文件以 `<?xml` 开头
            if content.startswith(b"<?xml"):
                return FileType.XML
            # 3、如果文件以 `{` 开头
            elif content.startswith(b'{"'):
                return FileType.JSON
        return FileType.OTHER

    def _get_file_action(
        self, local_file_path: str, modify_time: float
    ) -> FileActionEnum:
        """获取文件操作行为"""
        # 如果不存在，则下载
        if not osp.exists(local_file_path):
            return FileActionEnum.ADD

        # 如果已经存在，判断是否需要更新
        # 如果有道云笔记文件更新时间小于本地文件时间，说明没有更新，则不下载，跳过
        if modify_time <= osp.getmtime(local_file_path):
            logging.info(f"此文件「{local_file_path}」不更新，跳过")
            return FileActionEnum.CONTINUE

        # 同一目录存在同名 md 和 note 文件时，后更新文件将覆盖另一个
        return FileActionEnum.UPDATE

    @staticmethod
    def _optimize_file_name(name: str) -> str:
        """优化文件名"""
        # 替换下划线
        regex_symbol = re.compile(r"[<]")  # 符号： <
        # 删除特殊字符
        del_regex_symbol = re.compile(r'[\\/":\|\*\?#>]')  # 符号：\ / " : | * ? # >

        name = name.replace("\n", "")  # 去除换行符
        name = name.strip()  # 首尾的空格
        # 替换一些特殊符号
        name = regex_symbol.sub("_", name)
        name = del_regex_symbol.sub("", name)
        return name

    def pull_recursively(self):
        """
        根据目录 ID 循环遍历下载目录下所有文件
        :param dir_id:
        :param local_dir: 本地目录
        :return: error_msg
        """

        def inner(dir_id: Optional[str], local_dir: str):
            dir_info = SESSION.get_dir_info_by_id(dir_id)
            try:
                entries = dir_info["entries"]
            except KeyError:
                raise RuntimeError(
                    "有道云笔记修改了接口地址，此脚本暂时不能使用！请提 issue"
                )

            for entry in entries:
                file_entry = entry["fileEntry"]
                id = file_entry["id"]
                name = file_entry["name"]
                if file_entry["dir"]:
                    sub_dir = osp.join(local_dir, name).replace("\\", "/")
                    if not osp.exists(sub_dir):
                        os.mkdir(sub_dir)
                    inner(id, sub_dir)
                else:
                    modify_time = file_entry["modifyTimeForSort"]
                    create_time = file_entry["createTimeForSort"]
                    self._add_or_update_file(
                        id, name, local_dir, modify_time, create_time
                    )

        dir_id = self._get_ydnote_dir_id(CONFIG.ydnote_dir)
        inner(dir_id, self.root_local_dir)

    def _add_or_update_file(
        self, file_id, file_name, local_dir, modify_time, create_time
    ):
        file_name = self._optimize_file_name(file_name)
        youdao_file_suffix = osp.splitext(file_name)[1]  # 笔记后缀
        original_file_path = osp.join(local_dir, file_name).replace(
            "\\", "/"
        )  # 原后缀路径

        # 所有类型文件均下载，不做处理
        file_type = self._judge_type(file_id, youdao_file_suffix)

        # 「文档」类型本地文件均已 .md 结尾
        if file_type == FileType.OTHER:
            local_file_path = original_file_path
        else:
            name, _ = osp.splitext(file_name)
            local_file_path = osp.join(local_dir, f"{name}{MARKDOWN_SUFFIX}").replace(
                "\\", "/"
            )

        # 如果有有道云笔记是「文档」类型，则提示类型
        tip = ""
        if file_type != FileType.OTHER:
            tip = f"，云笔记原格式为 {file_type.name}"

        file_action = self._get_file_action(local_file_path, modify_time)
        if file_action == FileActionEnum.CONTINUE:
            return
        if file_action == FileActionEnum.UPDATE:
            # 考虑到使用 f.write() 直接覆盖原文件，在 Windows 下报错（WinError 183），先将其删除
            os.remove(local_file_path)
        try:
            self._pull_file(
                file_id,
                original_file_path,
                local_file_path,
                file_type,
                youdao_file_suffix,
            )
            if file_action == FileActionEnum.CONTINUE:
                logging.debug(
                    "{}「{}」{}".format(file_action.value, local_file_path, tip)
                )
            else:
                logging.info(
                    "{}「{}」{}".format(file_action.value, local_file_path, tip)
                )

            # 本地文件时间设置为有道云笔记的时间
            if platform.system() == "Windows":
                setctime(local_file_path, create_time)
            else:
                os.utime(local_file_path, (create_time, modify_time))

        except Exception as error:
            logging.info(
                "{}「{}」可能失败！请检查文件！错误提示：{}".format(
                    file_action.value, original_file_path, format(error)
                )
            )

    def _pull_file(
        self, file_id, file_path, local_file_path, file_type, youdao_file_suffix
    ):
        """
        下载文件
        :param file_id:
        :param file_path:
        :param local_file_path: 本地
        :param file_type:
        :param youdao_file_suffix:
        :return:
        """
        # 1、所有的都先下载
        response = SESSION.get_file_by_id(file_id)
        with open(file_path, "wb") as f:
            f.write(response.content)  # response.content 本身就是字节类型

        # 2、如果文件是 note 类型，将其转换为 MarkDown 类型
        if file_type == FileType.XML:
            try:
                YoudaoNoteConvert.covert_xml_to_markdown(file_path)
            except ET.ParseError:
                logging.info(
                    "此 note 笔记应该为 17 年以前新建，格式为 html，将转换为 Markdown ..."
                )
                YoudaoNoteConvert.covert_html_to_markdown(file_path)
            except Exception as e:
                logging.info("note 笔记转换 MarkDown 失败，将跳过", repr(e))
        elif file_type == FileType.JSON:
            YoudaoNoteConvert.covert_json_to_markdown(file_path)

        # 3、迁移文本文件里面的有道云笔记图片（链接）
        if file_type != FileType.OTHER or youdao_file_suffix == MARKDOWN_SUFFIX:
            imagePull = ImagePull(
                SESSION, self.smms_secret_token, self.is_relative_path
            )
            imagePull.migration_ydnote_url(local_file_path)
