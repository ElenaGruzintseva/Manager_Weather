from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PipelineAction(ABC):
    """Базовый класс для действий в пайплайне"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить действие, возвращает обновленный контекст"""
        pass

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Проверить, нужно ли выполнять действие"""
        return self.enabled

    def on_error(self, context: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """Обработать ошибку выполнения"""
        logger.error(f"Ошибка в действии пайплайна {self.name}: {str(error)}", exc_info=True)
        context['errors'] = context.get('errors', [])
        context['errors'].append({
            'action': self.name,
            'error': str(error),
        })
        return context


class PipelineContext:
    """Контекст выполнения пайплайна"""

    def __init__(self, initial_data: Dict[str, Any] = None):
        self.data = initial_data or {}


class PipelineManager:
    """Менеджер пайплайна"""

    def __init__(self):
        self.actions = []

    def register_action(self, action: PipelineAction):
        self.actions.append(action)
        logger.info(f"Зарегистрировано действие пайплайна: {action.name}")

    def execute(self, initial_context: Dict[str, Any] = None) -> PipelineContext:
        context = PipelineContext(initial_context or {})
        for action in self.actions:
            if not action.should_execute(context.data):
                logger.debug(f"Пропуск отключенного действия: {action.name}")
                continue

            try:
                logger.info(f"Выполнение действия: {action.name}")
                context.data = action.execute(context.data)
                logger.info(f"Действие {action.name} выполнено успешно")
            except Exception as e:
                context.data = action.on_error(context.data, e)
        return context
