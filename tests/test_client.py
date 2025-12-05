"""Tests for Naver Dictionary API client"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from naver_dict_api import (
    DictEntry,
    DictType,
    InvalidResponseError,
    NaverDictClient,
    NetworkError,
    ParseError,
    SearchMode,
    search_dict,
)


class TestDictEntry:
    """DictEntry 클래스 테스트"""

    def test_dict_entry_creation(self):
        """DictEntry 객체 생성 테스트"""
        entry = DictEntry(
            word="偀",
            reading="꽃부리 영",
            meanings=["꽃부리", "꾸미개", "싹"],
            entry_id="8c1bd80ffc8042c183e823b2171b1333",
            dict_type="ccko",
        )

        assert entry.word == "偀"
        assert entry.reading == "꽃부리 영"
        assert entry.meanings == ["꽃부리", "꾸미개", "싹"]
        assert entry.entry_id == "8c1bd80ffc8042c183e823b2171b1333"
        assert entry.dict_type == "ccko"

    def test_dict_entry_to_dict(self):
        """DictEntry.to_dict() 메서드 테스트"""
        entry = DictEntry(
            word="偀",
            reading="꽃부리 영",
            meanings=["꽃부리", "꾸미개", "싹"],
            entry_id="8c1bd80ffc8042c183e823b2171b1333",
            dict_type="ccko",
        )

        result = entry.to_dict()

        assert isinstance(result, dict)
        assert result["word"] == "偀"
        assert result["reading"] == "꽃부리 영"
        assert result["meanings"] == ["꽃부리", "꾸미개", "싹"]
        assert result["entry_id"] == "8c1bd80ffc8042c183e823b2171b1333"
        assert result["dict_type"] == "ccko"


class TestNaverDictClient:
    """NaverDictClient 클래스 테스트"""

    def test_client_initialization_default(self):
        """클라이언트 기본 초기화 테스트"""
        client = NaverDictClient()

        assert client.dict_type == DictType.HANJA
        assert client.search_mode == SearchMode.SIMPLE
        assert client.impersonate == "chrome136"
        assert client.base_url == "https://ac-dict.naver.com/ccko/ac"

    def test_client_initialization_custom(self):
        """클라이언트 커스텀 초기화 테스트"""
        client = NaverDictClient(
            dict_type=DictType.ENGLISH,
            search_mode=SearchMode.DETAILED,
            impersonate="chrome101",
        )

        assert client.dict_type == DictType.ENGLISH
        assert client.search_mode == SearchMode.DETAILED
        assert client.impersonate == "chrome101"
        assert client.base_url == "https://ac-dict.naver.com/enko/ac"

    def test_get_search_params_simple(self):
        """간단 모드 검색 파라미터 생성 테스트"""
        client = NaverDictClient(search_mode=SearchMode.SIMPLE)
        params = client._get_search_params("test")

        assert params["st"] == "11"
        assert params["r_lt"] == "10"
        assert params["q"] == "test"
        assert params["r_format"] == "json"
        assert params["r_enc"] == "UTF-8"

    def test_get_search_params_detailed(self):
        """상세 모드 검색 파라미터 생성 테스트"""
        client = NaverDictClient(search_mode=SearchMode.DETAILED)
        params = client._get_search_params("test")

        assert params["st"] == "111"
        assert params["r_lt"] == "111"
        assert params["q"] == "test"

    def test_safe_get_nested_valid(self):
        """_safe_get_nested 정상 케이스 테스트"""
        client = NaverDictClient()
        data = [["value1", "value2"], ["value3"]]

        assert client._safe_get_nested(data, 0, 0) == "value1"
        assert client._safe_get_nested(data, 0, 1) == "value2"
        assert client._safe_get_nested(data, 1, 0) == "value3"

    def test_safe_get_nested_invalid_index(self):
        """_safe_get_nested 잘못된 인덱스 테스트"""
        client = NaverDictClient()
        data = [["value1"]]

        assert client._safe_get_nested(data, 0, 5) == ""
        assert client._safe_get_nested(data, 5, 0) == ""

    def test_safe_get_nested_invalid_type(self):
        """_safe_get_nested 잘못된 타입 테스트"""
        client = NaverDictClient()
        data = [["value1"], "not_a_list"]

        assert client._safe_get_nested(data, 1, 0) == ""

    def test_get_referer_hanja(self):
        """한자 사전 Referer 헤더 테스트"""
        client = NaverDictClient(dict_type=DictType.HANJA)
        assert client._get_referer() == "https://hanja.dict.naver.com/"

    def test_get_referer_korean(self):
        """국어 사전 Referer 헤더 테스트"""
        client = NaverDictClient(dict_type=DictType.KOREAN)
        assert client._get_referer() == "https://ko.dict.naver.com/"

    def test_get_referer_english(self):
        """영어 사전 Referer 헤더 테스트"""
        client = NaverDictClient(dict_type=DictType.ENGLISH)
        assert client._get_referer() == "https://en.dict.naver.com/"

    def test_get_referer_default(self):
        """기본 Referer 헤더 테스트"""
        client = NaverDictClient(dict_type=DictType.GERMAN)
        assert client._get_referer() == "https://dict.naver.com/"

    @patch("naver_dict_api.client.requests.get")
    def test_search_success_hanja(self, mock_get):
        """한자 검색 성공 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                [
                    [
                        ["偀"],
                        ["꽃부리 영"],
                        [""],
                        ["꽃부리", "꾸미개", "싹"],
                        ["8c1bd80ffc8042c183e823b2171b1333"],
                        ["ccko"],
                    ]
                ]
            ]
        }
        mock_get.return_value = mock_response

        client = NaverDictClient(dict_type=DictType.HANJA)
        entry = client.search("偀")

        assert entry is not None
        assert entry.word == "偀"
        assert entry.reading == "꽃부리 영"
        assert entry.meanings == ["꽃부리", "꾸미개", "싹"]
        assert entry.entry_id == "8c1bd80ffc8042c183e823b2171b1333"
        assert entry.dict_type == "ccko"

    @patch("naver_dict_api.client.requests.get")
    def test_search_success_english(self, mock_get):
        """영어 검색 성공 테스트 (의미 인덱스가 다름)"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                [
                    [
                        ["hello"],
                        ["həˈloʊ"],
                        ["안녕", "여보세요"],
                        [],
                        ["test_id"],
                        ["enko"],
                    ]
                ]
            ]
        }
        mock_get.return_value = mock_response

        client = NaverDictClient(dict_type=DictType.ENGLISH)
        entry = client.search("hello")

        assert entry is not None
        assert entry.word == "hello"
        assert entry.reading == "həˈloʊ"
        assert entry.meanings == ["안녕", "여보세요"]

    @patch("naver_dict_api.client.requests.get")
    def test_search_no_results(self, mock_get):
        """검색 결과 없음 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [[]]}
        mock_get.return_value = mock_response

        client = NaverDictClient()
        entry = client.search("nonexistent")

        assert entry is None

    @patch("naver_dict_api.client.requests.get")
    def test_search_empty_items(self, mock_get):
        """빈 items 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = NaverDictClient()
        entry = client.search("test")

        assert entry is None

    @patch("naver_dict_api.client.requests.get")
    def test_search_network_error(self, mock_get):
        """네트워크 에러 테스트"""
        from curl_cffi.requests import RequestsError

        mock_get.side_effect = RequestsError("Network error")

        client = NaverDictClient()
        with pytest.raises(NetworkError, match="Failed to fetch data"):
            client.search("test")

    @patch("naver_dict_api.client.requests.get")
    def test_search_json_decode_error(self, mock_get):
        """JSON 디코딩 에러 테스트"""
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        client = NaverDictClient()
        with pytest.raises(ParseError, match="Failed to parse JSON response"):
            client.search("test")

    @patch("naver_dict_api.client.requests.get")
    def test_search_invalid_response_no_items(self, mock_get):
        """items 필드 없는 응답 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"query": "test"}
        mock_get.return_value = mock_response

        client = NaverDictClient()
        with pytest.raises(InvalidResponseError, match="missing 'items' field"):
            client.search("test")

    @patch("naver_dict_api.client.requests.get")
    def test_search_invalid_response_not_dict(self, mock_get):
        """딕셔너리가 아닌 응답 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = ["not", "a", "dict"]
        mock_get.return_value = mock_response

        client = NaverDictClient()
        with pytest.raises(InvalidResponseError, match="missing 'items' field"):
            client.search("test")

    @patch("naver_dict_api.client.requests.get")
    def test_search_invalid_item_structure(self, mock_get):
        """잘못된 item 구조 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [["not_a_valid_item"]]}
        mock_get.return_value = mock_response

        client = NaverDictClient()
        with pytest.raises(InvalidResponseError, match="Invalid item structure"):
            client.search("test")

    @patch("naver_dict_api.client.requests.get")
    def test_search_calls_api_with_correct_params(self, mock_get):
        """API 호출 시 올바른 파라미터 전달 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = NaverDictClient(
            dict_type=DictType.KOREAN, search_mode=SearchMode.DETAILED
        )
        client.search("안녕")

        mock_get.assert_called_once()
        call_args = mock_get.call_args

        assert call_args[0][0] == "https://ac-dict.naver.com/koko/ac"
        assert call_args[1]["params"]["q"] == "안녕"
        assert call_args[1]["params"]["st"] == "111"
        assert call_args[1]["params"]["r_lt"] == "111"
        assert call_args[1]["headers"]["referer"] == "https://ko.dict.naver.com/"


class TestSearchDict:
    """search_dict 함수 테스트"""

    @patch("naver_dict_api.client.requests.get")
    def test_search_dict_default(self, mock_get):
        """search_dict 기본 파라미터 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                [
                    [
                        ["偀"],
                        ["꽃부리 영"],
                        [""],
                        ["꽃부리"],
                        ["test_id"],
                        ["ccko"],
                    ]
                ]
            ]
        }
        mock_get.return_value = mock_response

        entry = search_dict("偀")

        assert entry is not None
        assert entry.word == "偀"
        assert entry.dict_type == "ccko"

    @patch("naver_dict_api.client.requests.get")
    def test_search_dict_custom_params(self, mock_get):
        """search_dict 커스텀 파라미터 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                [
                    [
                        ["hello"],
                        ["həˈloʊ"],
                        ["안녕"],
                        [],
                        ["test_id"],
                        ["enko"],
                    ]
                ]
            ]
        }
        mock_get.return_value = mock_response

        entry = search_dict(
            "hello",
            dict_type=DictType.ENGLISH,
            search_mode=SearchMode.DETAILED,
            impersonate="chrome101",
        )

        assert entry is not None
        assert entry.word == "hello"

        call_args = mock_get.call_args
        assert call_args[0][0] == "https://ac-dict.naver.com/enko/ac"
        assert call_args[1]["params"]["st"] == "111"


class TestDictType:
    """DictType Enum 테스트"""

    def test_dict_type_values(self):
        """DictType 값 테스트"""
        assert DictType.HANJA.value == "ccko"
        assert DictType.KOREAN.value == "koko"
        assert DictType.ENGLISH.value == "enko"
        assert DictType.JAPANESE.value == "jako"
        assert DictType.CHINESE.value == "zhko"
        assert DictType.GERMAN.value == "deko"
        assert DictType.FRENCH.value == "frko"
        assert DictType.SPANISH.value == "esko"
        assert DictType.RUSSIAN.value == "ruko"
        assert DictType.VIETNAMESE.value == "viko"
        assert DictType.ITALIAN.value == "itko"
        assert DictType.THAI.value == "thko"
        assert DictType.INDONESIAN.value == "idko"
        assert DictType.UZBEK.value == "uzko"


class TestSearchMode:
    """SearchMode Enum 테스트"""

    def test_search_mode_values(self):
        """SearchMode 값 테스트"""
        assert SearchMode.SIMPLE.value == "simple"
        assert SearchMode.DETAILED.value == "detailed"


@pytest.mark.integration
class TestIntegration:
    """실제 API 통합 테스트"""

    def test_search_hanja_real(self):
        """실제 한자 검색 통합 테스트"""
        client = NaverDictClient(dict_type=DictType.HANJA)
        entry = client.search("偀")

        assert entry is not None
        assert entry.word == "偀"
        assert len(entry.reading) > 0
        assert len(entry.meanings) > 0
        assert entry.dict_type == "ccko"

    def test_search_korean_real(self):
        """실제 국어 검색 통합 테스트"""
        entry = search_dict("안녕", dict_type=DictType.KOREAN)

        assert entry is not None
        assert "안녕" in entry.word
        assert len(entry.meanings) > 0

    def test_search_english_real(self):
        """실제 영어 검색 통합 테스트"""
        entry = search_dict("hello", dict_type=DictType.ENGLISH)

        assert entry is not None
        assert "hello" in entry.word.lower()
        assert len(entry.meanings) > 0

    def test_search_nonexistent_real(self):
        """존재하지 않는 단어 검색 통합 테스트"""
        entry = search_dict("xyzabc123nonexistent", dict_type=DictType.HANJA)

        assert entry is None

    def test_search_detailed_mode_real(self):
        """상세 모드 검색 통합 테스트"""
        client = NaverDictClient(
            dict_type=DictType.HANJA, search_mode=SearchMode.DETAILED
        )
        entry = client.search("前")

        assert entry is not None
        assert entry.word == "前"
