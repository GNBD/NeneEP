
Nene EasyPort 🪶
Nene EasyPort는 마크서버 초보운영자들을 위한 초간단 UPnP 포트 포워딩 도구입니다. 복잡한 공유기 설정 없이 버튼 하나로 25565 포트를 개방할 수 있습니다.
(공유기에서 UPnP 기능이 활성화 되어있어야합니다. (보통기본으로 활성화되어있음))

<img width="398" height="652" alt="image" src="https://github.com/user-attachments/assets/aac2635a-e4f5-4eec-b1e5-0947fecac450" />

✨ 기능 (Features)
• 자동 포트 포워딩: UPnP를 사용하여 25565 포트 자동 개방
• IP 주소 확인: 내 외부 IP(Public IP)와 내부 IP(Local IP) 즉시 확인
• 가벼운 용량: Python 기반의 가볍고 빠른 실행


🛠️ 설치 및 실행 (How to Run)
필수 요구 사항
Python 3.x

miniupnpc 라이브러리

라이브러리 설치
``pip install miniupnpc``
실행
``python NeneEP.py``

이 프로그램은 miniupnpc (BSD License) 라이브러리를 포함하고 있습니다.
