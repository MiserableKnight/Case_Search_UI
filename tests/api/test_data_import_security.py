"""数据导入路由的路径穿越防护回归测试。

覆盖两个高危修复：
- 上传文件名剥离目录成分，文件不得写出临时目录之外
- confirm 接口的 temp_id 必须为 UUID 格式
"""

import io
import json
import os
import tempfile
import uuid

import pytest


@pytest.mark.api
class TestUploadFilenameTraversal:
    """上传文件名的路径穿越防护"""

    def test_traversal_filename_stripped_to_basename(self, client):
        """带 ../ 的恶意文件名不得把文件写出本次请求的临时目录之外"""
        unique_name = f"trav_{uuid.uuid4().hex}.xls"
        malicious_filename = f"../{unique_name}"
        # 修复前的落盘位置（临时根目录的上一层），修复后不应有文件出现在这里
        escaped_path = os.path.join(tempfile.gettempdir(), "case_search_ui_temp", unique_name)

        response = client.post(
            "/api/import/case/import",
            data={"file": (io.BytesIO(b"not a real excel"), malicious_filename)},
            content_type="multipart/form-data",
        )

        # 文件内容不是合法 Excel，分析必然失败；关键是文件不得落在临时目录之外
        assert response.status_code in (400, 500)
        assert not os.path.exists(escaped_path), f"文件被写出临时目录: {escaped_path}"

    def test_normal_chinese_filename_still_accepted(self, client):
        """中文业务文件名不应被消毒逻辑破坏（secure_filename 会丢弃中文）"""
        unique_stem = uuid.uuid4().hex[:8]
        response = client.post(
            "/api/import/case/import",
            data={"file": (io.BytesIO(b"not a real excel"), f"服务请求报表{unique_stem}.xls")},
            content_type="multipart/form-data",
        )

        # 走到分析阶段才失败（内容非法），而不是被文件名校验拦截
        assert response.status_code in (400, 500)
        data = json.loads(response.data)
        assert data["message"] != "无效的文件名"


@pytest.mark.api
class TestConfirmTempIdValidation:
    """confirm 接口的 temp_id 校验"""

    def test_path_traversal_temp_id_rejected(self, client):
        """路径穿越形式的 temp_id 必须被拒绝"""
        response = client.post(
            "/api/import/case/confirm",
            json={"temp_id": "../.."},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["message"] == "无效的临时文件ID"

    def test_non_uuid_temp_id_rejected(self, client):
        """非 UUID 格式的 temp_id 必须被拒绝"""
        response = client.post(
            "/api/import/case/confirm",
            json={"temp_id": "not-a-uuid"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["message"] == "无效的临时文件ID"

    def test_valid_uuid_temp_id_passes_format_check(self, client):
        """合法 UUID 但不存在的临时目录：应走到"找不到临时数据"而非格式拒绝"""
        response = client.post(
            "/api/import/case/confirm",
            json={"temp_id": str(uuid.uuid4())},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["message"] == "无法找到临时数据，请重新预览"
