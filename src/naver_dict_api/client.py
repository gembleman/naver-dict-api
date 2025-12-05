"""Naver Dictionary API Client"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, cast

from curl_cffi import BrowserTypeLiteral, requests


class NaverDictError(Exception):
    """Naver 사전 API 관련 기본 예외"""


class NetworkError(NaverDictError):
    """네트워크 요청 실패 예외"""


class ParseError(NaverDictError):
    """응답 파싱 실패 예외"""


class InvalidResponseError(NaverDictError):
    """API 응답 형식이 올바르지 않을 때 발생하는 예외"""


class DictType(Enum):
    """사전 타입"""

    HANJA = "ccko"  # 한자
    KOREAN = "koko"  # 국어
    ENGLISH = "enko"  # 영어
    JAPANESE = "jako"  # 일본어
    CHINESE = "zhko"  # 중국어
    GERMAN = "deko"  # 독일어
    FRENCH = "frko"  # 프랑스어
    SPANISH = "esko"  # 스페인어
    RUSSIAN = "ruko"  # 러시아어
    VIETNAMESE = "viko"  # 베트남어
    ITALIAN = "itko"  # 이탈리아어
    THAI = "thko"  # 태국어
    INDONESIAN = "idko"  # 인도네시아어
    UZBEK = "uzko"  # 우즈베키스탄어


class SearchMode(Enum):
    """검색 상세도 모드"""

    SIMPLE = "simple"  # 간단 모드 (st=11, r_lt=10)
    DETAILED = "detailed"  # 상세 모드 (st=111, r_lt=111)


@dataclass
class DictEntry:
    """사전 항목 정보를 담는 데이터 클래스"""

    word: str  # 단어/한자
    reading: str  # 발음/읽기
    meanings: list[str]  # 의미 목록
    entry_id: str  # 항목 ID
    dict_type: str  # 사전 타입

    def to_dict(self) -> dict[str, str | list[str]]:
        """딕셔너리로 변환"""
        return {
            "word": self.word,
            "reading": self.reading,
            "meanings": self.meanings,
            "entry_id": self.entry_id,
            "dict_type": self.dict_type,
        }


class NaverDictClient:
    """Naver 사전 API 통합 클라이언트"""

    BASE_URL_TEMPLATE: Final[str] = "https://ac-dict.naver.com/{dict_type}/ac"
    DEFAULT_TIMEOUT: Final[int] = 30  # 30초

    def __init__(
        self,
        dict_type: DictType = DictType.HANJA,
        search_mode: SearchMode = SearchMode.SIMPLE,
        impersonate: BrowserTypeLiteral | None = "chrome136",
        timeout: int | None = None,
    ) -> None:
        """
        Args:
            dict_type: 사전 타입 (기본값: 한자)
            search_mode: 검색 모드 (기본값: 간단)
            impersonate: curl_cffi에서 사용할 브라우저 타입 (기본값: "chrome136")
            timeout: 요청 타임아웃 (초 단위, 기본값: 30초)
        """
        self.dict_type = dict_type
        self.search_mode = search_mode
        self.impersonate = impersonate
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.base_url = self.BASE_URL_TEMPLATE.format(dict_type=dict_type.value)

    def _get_search_params(self, query: str) -> dict[str, str]:
        """검색 모드에 따른 파라미터 생성"""
        if self.search_mode == SearchMode.SIMPLE:
            st, r_lt = "11", "10"
        else:  # DETAILED
            st, r_lt = "111", "111"

        return {
            "st": st,
            "r_lt": r_lt,
            "q": query,
            "r_format": "json",
            "r_enc": "UTF-8",
        }

    def _safe_get_nested(self, item: list[Any], *indices: int) -> str:
        """중첩된 리스트에서 안전하게 값을 추출

        Args:
            item: 추출할 리스트
            indices: 접근할 인덱스 순서

        Returns:
            추출된 문자열 또는 빈 문자열
        """
        try:
            current = item
            for idx in indices:
                if not isinstance(current, list) or len(current) <= idx:
                    return ""
                current = current[idx]
            return str(current) if current else ""
        except (IndexError, TypeError):
            return ""

    def _get_referer(self) -> str:
        """사전 타입에 따른 Referer 헤더 생성"""
        referer_map = {
            DictType.HANJA: "https://hanja.dict.naver.com/",
            DictType.KOREAN: "https://ko.dict.naver.com/",
            DictType.ENGLISH: "https://en.dict.naver.com/",
            DictType.JAPANESE: "https://ja.dict.naver.com/",
            DictType.CHINESE: "https://zh.dict.naver.com/",
        }
        return referer_map.get(self.dict_type, "https://dict.naver.com/")

    def search(self, query: str) -> DictEntry | None:
        """단어/한자를 검색하여 정보를 반환

        Args:
            query: 검색할 단어/한자 (예: "偀", "안녕", "hello")

        Returns:
            DictEntry 객체 또는 None (결과가 없을 경우)

        Raises:
            NetworkError: 네트워크 요청 실패 시
            ParseError: 응답 파싱 실패 시
            InvalidResponseError: API 응답 형식이 올바르지 않을 때
        """
        params = self._get_search_params(query)

        headers = {
            "accept": "*/*",
            "accept-language": "ko;q=0.6",
            "referer": self._get_referer(),
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                impersonate=cast(BrowserTypeLiteral | None, self.impersonate),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestsError as e:
            msg = f"Failed to fetch data from Naver Dict API: {e}"
            raise NetworkError(msg) from e

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON response: {e}"
            raise ParseError(msg) from e

        # API 응답 구조 검증
        if not isinstance(data, dict) or "items" not in data:
            msg = "Invalid API response structure: missing 'items' field"
            raise InvalidResponseError(msg)

        items = data.get("items", [[]])
        if not isinstance(items, list) or len(items) == 0:
            return None

        first_group = items[0]
        if not isinstance(first_group, list) or len(first_group) == 0:
            return None

        item = first_group[0]
        if not isinstance(item, list):
            msg = "Invalid item structure in API response"
            raise InvalidResponseError(msg)

        # 사전 타입에 따라 의미 인덱스가 다름
        meanings_idx = 2 if self.dict_type == DictType.ENGLISH else 3

        # 안전한 배열 접근으로 데이터 추출
        return DictEntry(
            word=self._safe_get_nested(item, 0, 0),
            reading=self._safe_get_nested(item, 1, 0),
            meanings=(
                item[meanings_idx]
                if len(item) > meanings_idx and isinstance(item[meanings_idx], list)
                else []
            ),
            entry_id=self._safe_get_nested(item, 4, 0),
            dict_type=self.dict_type.value,
        )


def search_dict(
    query: str,
    dict_type: DictType = DictType.HANJA,
    search_mode: SearchMode = SearchMode.SIMPLE,
    *,
    impersonate: BrowserTypeLiteral | None = "chrome136",
    timeout: int | None = None,
) -> DictEntry | None:
    """다중 언어 사전 검색 함수

    Args:
        query: 검색할 단어/한자 (예: "偀", "안녕", "hello")
        dict_type: 사전 타입 (기본값: 한자)
        search_mode: 검색 모드 (기본값: 간단)
        impersonate: curl_cffi에서 사용할 브라우저 타입 (기본값: "chrome136")
        timeout: 요청 타임아웃 (초 단위, 기본값: 30초)

    Returns:
        DictEntry 객체 또는 None (결과가 없을 경우)

    Example:
        >>> from naver_hanja import search_dict, DictType, SearchMode
        >>> # 한자 검색
        >>> entry = search_dict("偀", DictType.HANJA)
        >>> # 국어 검색
        >>> entry = search_dict("안녕", DictType.KOREAN)
        >>> # 영어 검색 (상세 모드)
        >>> entry = search_dict("hello", DictType.ENGLISH, SearchMode.DETAILED)
        >>> if entry:
        ...     print(entry.word)
        ...     print(entry.meanings)
    """
    client = NaverDictClient(
        dict_type=dict_type,
        search_mode=search_mode,
        impersonate=impersonate,
        timeout=timeout,
    )
    return client.search(query)
