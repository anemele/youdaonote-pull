import logging
import sys
import time
import traceback

import requests

from youdaonote_pull import YoudaoNotePull, log

log.init_logging()

start_time = int(time.time())

try:
    youdaonote_pull = YoudaoNotePull()
    ydnote_dir_id, error_msg = youdaonote_pull.get_ydnote_dir_id()
    if error_msg:
        logging.info(error_msg)
        sys.exit(1)
    logging.info("正在 pull，请稍后 ...")
    youdaonote_pull.pull_dir_by_id_recursively(
        ydnote_dir_id, youdaonote_pull.root_local_dir
    )
except requests.exceptions.ProxyError:
    logging.info(
        "请检查网络代理设置；也有可能是调用有道云笔记接口次数达到限制，请等待一段时间后重新运行脚本，若一直失败，可删除「cookies.json」后重试"
    )
    traceback.print_exc()
    logging.info("已终止执行")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    logging.info(
        "网络错误，请检查网络是否正常连接。若突然执行中断，可忽略此错误，重新运行脚本"
    )
    traceback.print_exc()
    logging.info("已终止执行")
    sys.exit(1)
# 链接错误等异常
except Exception as err:
    logging.info("Cookies 可能已过期！其他错误：", format(err))
    traceback.print_exc()
    logging.info("已终止执行")
    sys.exit(1)

end_time = int(time.time())
logging.info("运行完成！耗时 {} 秒".format(str(end_time - start_time)))
