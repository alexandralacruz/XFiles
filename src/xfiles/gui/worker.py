"""Ejecución de tareas largas en segundo plano (sin bloquear la interfaz)."""

from __future__ import annotations

import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    """Envuelve una función en un QRunnable y emite el resultado o el error."""

    def __init__(self, fn: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:  # noqa: D102
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.signals.error.emit(str(exc) or exc.__class__.__name__)
        else:
            self.signals.finished.emit(result)


def run_in_background(fn: Callable, *args, **kwargs) -> Worker:
    """Lanza `fn` en el pool global y devuelve el Worker (con .signals)."""
    worker = Worker(fn, *args, **kwargs)
    QThreadPool.globalInstance().start(worker)
    return worker
