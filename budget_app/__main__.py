"""
[budget_app 패키지 실행 진입점 (Entry Point)]

💡 파이썬 기초 문법 설명:
1. __main__.py의 역할:
   - 사용자가 터미널에서 `python -m budget_app` 명령어를 입력했을 때,
     파이썬 인터프리터가 해당 패키지 안에서 가장 먼저 자동으로 찾아 실행하는 특수 파일입니다.
2. if __name__ == "__main__": 구조:
   - 파이썬 파일이 터미널에서 '직접 실행'될 때, 내장 특수 변수 `__name__`에는 문자열 `"__main__"`이 할당됩니다.
   - 반대로 다른 파일에서 이 파일을 `import`해서 불러올 때는 파일 이름(`budget_app.__main__`)이 들어갑니다.
   - 따라서 이 조건문은 "이 파일이 직접 실행되었을 때만 아래 main() 함수를 실행하라"는 안전장치 역할을 합니다.
"""

from budget_app.cli import main

if __name__ == "__main__":
    main()
