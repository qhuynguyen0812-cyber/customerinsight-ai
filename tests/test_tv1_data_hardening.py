"""Phase 2 evidence for atomic FastAPI dataset uploads owned by TV1."""

from __future__ import annotations

import asyncio
import io
import json
import re

import pytest
from starlette.datastructures import UploadFile
from starlette.requests import Request

from web.app import get_state, upload_dataset


def make_request(method: str, path: str, session_id: str) -> Request:
    async def receive():
        return {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }

    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [
                (b"host", b"testserver"),
                (
                    b"cookie",
                    f"customerinsight_session={session_id}".encode("latin1"),
                ),
            ],
        },
        receive,
    )


def get_session_id(response) -> str:
    cookie = response.headers.get("set-cookie", "")
    match = re.search(
        r"customerinsight_session=([a-f0-9]+)",
        cookie,
    )
    assert match is not None
    return match.group(1)


def upload_csv(
    payload: bytes,
    session_id: str,
    filename: str = "customers.csv",
):
    file = UploadFile(
        filename=filename,
        file=io.BytesIO(payload),
    )

    return asyncio.run(
        upload_dataset(
            make_request(
                "POST",
                "/api/dataset/upload",
                session_id,
            ),
            file,
        )
    )


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        (
            b"",
            "trống",
        ),
        (
            b'CustomerID,Recency,Frequency,Monetary\n'
            b'C1,"unterminated,2,3',
            "Không thể đọc",
        ),
        (
            b"CustomerID,Recency,Frequency\n"
            b"C1,10,5\n",
            "Thiếu cột bắt buộc",
        ),
        (
            b"CustomerID,Recency,Frequency,Monetary\n"
            b"C1,10,5,100\n"
            b"C1,20,2,50\n",
            "ánh xạ 1:1",
        ),
        (
            b"CustomerID,Recency,Frequency,Monetary\n"
            b"C1,abc,5,100\n",
            "không phải số",
        ),
        (
            b"CustomerID,Recency,Frequency,Monetary\n"
            b"C1,-1,5,100\n",
            "giá trị âm",
        ),
        (
            b"CustomerID,Recency,Frequency,Monetary\n"
            b"C1,10,5,inf\n",
            "vô cực",
        ),
    ],
)
def test_failed_upload_preserves_previous_valid_api_state(
    payload: bytes,
    expected_detail: str,
) -> None:
    valid = (
        b"CustomerID,Recency,Frequency,Monetary\n"
        b"C1,10,5,100\n"
        b"C2,20,2,50\n"
        b"C3,30,8,200\n"
    )

    first_response = upload_csv(
        valid,
        "tv1-phase2-seed",
    )

    assert first_response.status_code == 200

    session_id = get_session_id(first_response)
    state_before = json.loads(first_response.body)

    failed_response = upload_csv(
        payload,
        session_id,
    )

    assert failed_response.status_code == 422

    error_detail = json.loads(
        failed_response.body
    )["detail"]

    assert expected_detail in error_detail

    current_response = get_state(
        make_request(
            "GET",
            "/api/state",
            session_id,
        )
    )

    assert current_response.status_code == 200

    state_after = json.loads(current_response.body)

    assert state_after["dataset_loaded"] is True
    assert state_after["row_count"] == 3

    assert (
        state_after["dataset_signature"]
        == state_before["dataset_signature"]
    )

    assert (
        state_after["preview"]
        == state_before["preview"]
    )


def test_mixed_headers_and_extra_columns_are_accepted_through_api():
    payload = (
        b" customerid ,RECENCY,frequency ,Monetary,Ignored\n"
        b"0012,10,5,100,x\n"
        b"C2,20,2,50,y\n"
    )

    response = upload_csv(
        payload,
        "tv1-phase2-headers",
    )

    assert response.status_code == 200

    state = json.loads(response.body)

    assert state["row_count"] == 2
    assert state["preview"][0]["CustomerID"] == "0012"
    assert "Ignored" not in state["preview"][0]