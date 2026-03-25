"""
Конфигурация pytest для тестов.
"""
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для импортов
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
