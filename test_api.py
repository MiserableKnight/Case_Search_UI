import json
from typing import Optional

import requests


def test_api() -> None:
    try:
        # 测试获取数据列
        response = requests.get("http://localhost:5000/api/data_columns?source=case")
        print("API响应状态码:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print("API响应内容:", json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("API响应错误:", response.text)
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")


if __name__ == "__main__":
    test_api()
