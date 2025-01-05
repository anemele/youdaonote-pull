import logging
import sys
import time
import traceback

from requests.exceptions import ConnectionError, ProxyError

from .core import YoudaoNotePull


def main():
    start_time = time.perf_counter()

    try:
        youdaonote_pull = YoudaoNotePull()
        logging.info("正在 pull，请稍后 ...")
        youdaonote_pull.pull_recursively()
    except ProxyError:
        logging.info(
            "请检查网络代理设置；也有可能是调用有道云笔记接口次数达到限制，请等待一段时间后重新运行脚本，"
            "若一直失败，可删除「cookies.json」后重试"
        )
        traceback.print_exc()
        logging.info("已终止执行")
        sys.exit(1)
    except ConnectionError:
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

    end_time = time.perf_counter()
    logging.info(f"运行完成！耗时 {end_time - start_time:.3} 秒")
