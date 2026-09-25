"""
[외부 정렬 및 K-way 병합 스트리밍 모듈 (sort_utils.py)]

💡 파이썬 기초 문법 및 컴퓨터 공학(CS) 알고리즘 설명:
1. 외부 정렬 (External Merge Sort):
   - 데이터 크기가 RAM 용량을 초과하거나, 대용량 파일에서 메모리 사용량을 O(1)로 엄격히 통제해야 할 때 사용하는 정렬 기법입니다.
   - 전체 데이터를 한 번에 `list()`로 메모리에 적재하지 않고, 지정된 `chunk_size` 단위로 분할하여 정렬한 뒤
     임시 파일에 기록하고, `heapq.merge`를 통해 K-way 병합 스트리밍을 수행합니다.
2. heapq.merge (K-way 병합):
   - 파이썬 표준 라이브러리 `heapq.merge`는 이미 정렬된 K개의 제너레이터/이터레이터를 인자로 받아,
     최소/최대 힙(Heap)을 이용해 O(log K) 시간 복잡도로 원소를 하나씩 스트리밍(yield)합니다.
   - 메모리에는 각 파일의 현재 가리키는 1개 원소(총 K개)만 적재되므로,
     100,000건(100k+) 이상의 데이터라도 메모리 사용량이 극도로 작게(O(K)) 유지됩니다.
3. 소량 데이터 패스트 패스 (Fast-Path Optimization):
   - 전체 데이터 개수가 `chunk_size`(예: 1,000건) 이하인 경우, 불필요한 디스크 I/O 임시 파일 생성 없이
     인메모리에서 즉시 정렬하여 yield함으로써 소량 데이터에서의 실행 속도(0.001초 미만)를 극대화합니다.
"""

import heapq
import json
import os
import tempfile
from typing import Generator, Iterable, Callable, Any, List

def external_merge_sort(
    iterable: Iterable[Any],
    key: Callable[[Any], Any],
    reverse: bool = True,
    chunk_size: int = 1000,
    serializer: Callable[[Any], dict] = lambda x: x.__dict__,
    deserializer: Callable[[dict], Any] = None
) -> Generator[Any, None, None]:
    """
    [외부 정렬 및 K-way 병합 스트리밍 제너레이터]
    - 대용량 데이터 전체를 list()로 메모리에 로드하지 않고 chunk_size 단위로 나누어 정렬
    - 청크가 1개인 경우(소량 데이터): 파일 생성 없이 인메모리 정렬 후 즉시 yield
    - 청크가 2개 이상인 경우(대용량 데이터): 청크별 임시 파일 기록 후 heapq.merge로 O(K) 스트리밍 병합
    - 종료 또는 break 시 임시 파일 자동 정리(Clean-up) 보장
    """
    iterator = iter(iterable)
    first_chunk: List[Any] = []
    
    # 첫 번째 청크 읽기
    for _ in range(chunk_size):
        try:
            first_chunk.append(next(iterator))
        except StopIteration:
            break
            
    # 데이터가 chunk_size 이하인 경우 (소량 데이터 패스트 패스)
    try:
        next_item = next(iterator)
    except StopIteration:
        first_chunk.sort(key=key, reverse=reverse)
        yield from first_chunk
        return

    # 데이터가 chunk_size를 초과하는 대용량인 경우: 임시 파일 분할 후 K-way 병합
    temp_files: List[str] = []
    
    def _write_chunk_to_temp(chunk: List[Any]) -> str:
        chunk.sort(key=key, reverse=reverse)
        fd, temp_path = tempfile.mkstemp(prefix="sort_chunk_", suffix=".jsonl", text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            for item in chunk:
                data = serializer(item) if serializer else item
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return temp_path

    try:
        # 첫 번째 청크를 정렬하여 임시 파일로 플러시
        temp_files.append(_write_chunk_to_temp(first_chunk))
        
        # 나머지 데이터도 chunk_size 단위로 청크 정렬하여 임시 파일 기록
        current_chunk = [next_item]
        for item in iterator:
            current_chunk.append(item)
            if len(current_chunk) >= chunk_size:
                temp_files.append(_write_chunk_to_temp(current_chunk))
                current_chunk = []
        if current_chunk:
            temp_files.append(_write_chunk_to_temp(current_chunk))

        # 각 임시 파일로부터 한 줄씩 스트리밍 읽는 제너레이터 생성 함수
        def _read_temp_chunk(path: str) -> Generator[Any, None, None]:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        yield deserializer(data) if deserializer else data

        chunk_generators = [_read_temp_chunk(p) for p in temp_files]

        # heapq.merge를 활용한 K-way 병합 스트리밍 (메모리에는 K개의 원소만 상주)
        merged_stream = heapq.merge(*chunk_generators, key=key, reverse=reverse)
        for item in merged_stream:
            yield item

    finally:
        # 순회 종료 또는 break 중단 시 임시 파일 즉시 완전 삭제
        for p in temp_files:
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass
