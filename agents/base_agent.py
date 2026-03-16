from abc import ABC, abstractmethod
from typing import Any
from env.engine import PuertoRicoGame

class BaseAgent(ABC):
    """
    푸에르토리코 게임의 모든 에이전트가 상속받아야 하는 추상 기본 클래스(Abstract Base Class)입니다.
    이를 통해 강화학습(RL), 휴리스틱, MCTS 등 통일된 MLOps 인터페이스로 평가할 수 있습니다.
    """
    def __init__(self, player_idx: int):
        self.player_idx = player_idx

    @abstractmethod
    def get_action(self, state: PuertoRicoGame) -> Any:
        """
        주어진 게임 상태(state)에서 이 에이전트가 선택할 최적의 액션을 반환해야 합니다.
        """
        pass
