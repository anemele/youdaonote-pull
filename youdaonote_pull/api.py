import json

import requests


class YoudaoNoteApi(object):
    """
    有道云笔记 API 封装
    原理：https://depp.wang/2020/06/11/how-to-find-the-api-of-a-website-eg-note-youdao-com/
    """

    ROOT_ID_URL = "https://note.youdao.com/yws/api/personal/file?method=getByPath&keyfrom=web&cstk={cstk}"
    DIR_MES_URL = (
        "https://note.youdao.com/yws/api/personal/file/{dir_id}?all=true&f=true&len=1000&sort=1"
        "&isReverse=false&method=listPageByParentId&keyfrom=web&cstk={cstk}"
    )
    FILE_URL = (
        "https://note.youdao.com/yws/api/personal/sync?method=download&_system=macos&_systemVersion=&"
        "_screenWidth=1280&_screenHeight=800&_appName=ynote&_appuser=0123456789abcdeffedcba9876543210&"
        "_vendor=official-website&_launch=16&_firstTime=&_deviceId=0123456789abcdef&_platform=web&"
        "_cityCode=110000&_cityName=&sev=j1&keyfrom=web&cstk={cstk}"
    )

    def __init__(self, cookies_path=None):
        cookies_path = cookies_path or "cookies.json"
        with open(cookies_path, "rb") as fp:
            cookies_dict = json.load(fp)

        try:
            cookies = cookies_dict["cookies"]
        except KeyError:
            raise Exception(f"转换「{cookies_path}」为字典时出现错误")

        self._session = requests.Session()  # 使用 session 维持有道云笔记的登陆状态
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/100.0.4896.88 Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
            }
        )

        for cookie in cookies:
            self._session.cookies.set(
                name=cookie[0], value=cookie[1], domain=cookie[2], path=cookie[3]
            )

        # cstk 用于请求时接口验证
        if "YNOTE_CSTK" == cookies[0][0]:
            self._cstk = cookies[0][1]
        else:
            raise ValueError("YNOTE_CSTK 字段为空")

    def login_by_cookies(self):
        pass

    def http_post(self, url, data=None, files=None):
        """
        封装 post 请求
        :param url:
        :param data:
        :param files:
        :return: response
        """
        return self._session.post(url, data=data, files=files)

    def http_get(self, url):
        """
        封装 get 请求
        :param url:
        :return: response
        """
        return self._session.get(url)

    def get_root_dir_info_id(self) -> dict:
        """
        获取有道云笔记根目录信息
        :return: {
            'fileEntry': {'id': 'test_root_id', 'name': 'ROOT', ...},
            ...
        }
        """
        data = {"path": "/", "entire": "true", "purge": "false", "cstk": self._cstk}
        resp = self.http_post(self.ROOT_ID_URL.format(cstk=self._cstk), data=data)
        return resp.json()

    def get_dir_info_by_id(self, dir_id) -> dict:
        """
        根据目录 ID 获取目录下所有文件信息
        :return: {
            'count': 3,
            'entries': [
                 {'fileEntry': {'id': 'test_dir_id', 'name': 'test_dir', 'dir': true, ...}},
                 {'fileEntry': {'id': 'test_note_id', 'name': 'test_note', 'dir': false, ...}}
                 ...
            ]
        }
        """
        url = self.DIR_MES_URL.format(dir_id=dir_id, cstk=self._cstk)
        return self.http_get(url).json()

    def get_file_by_id(self, file_id):
        """
        根据文件 ID 获取文件内容
        :param file_id:
        :return: response，内容为笔记字节码
        """
        url = self.FILE_URL.format(cstk=self._cstk)
        data = {
            "fileId": file_id,
            "version": -1,
            "convert": "true",
            "editorType": 1,
            "cstk": self._cstk,
        }
        return self.http_post(url, data=data)
