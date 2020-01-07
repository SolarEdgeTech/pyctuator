import sys
import threading
from threading import Thread
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class StackFrame:
    methodName: str
    fileName: str
    lineNumber: int
    className: Optional[str]
    nativeMethod: bool


@dataclass
class ThreadInfo:
    threadName: str
    threadId: Optional[int]
    daemon: bool
    suspended: bool
    threadState: str
    stackTrace: List[StackFrame]


@dataclass
class ThreadDump:
    threads: List[ThreadInfo]


class ThreadDumpProvider:

    # pylint: disable=protected-access
    def get_thread_dump(self) -> ThreadDump:
        frames: Dict[Any, Any] = sys._current_frames()
        return ThreadDump([
            self._extract_thread_info(frames, thread)
            for thread in threading.enumerate()
        ])

    def _extract_thread_info(self, frames: Dict[Any, Any], thread: Thread) -> ThreadInfo:
        return ThreadInfo(
            threadName=thread.name,
            threadId=thread.ident,
            daemon=thread.daemon,
            suspended=not thread.is_alive(),
            threadState=self._calc_thread_state(thread),
            stackTrace=self._build_thread_stack_trace(thread, frames),
        )

    def _build_thread_stack_trace(self, thread: Thread, frames: Dict[Any, Any]) -> List[StackFrame]:

        def guess_class_name() -> Optional[str]:
            """
            Tries to find a class name if one exists.
            Fails if the frame is not in a class, or if the method does not call itself "self"
            Does not support static and class methods.
            """
            try:
                return str(frame.f_locals["self"].__class__.__name__)
            except KeyError:
                return None

        stack_frames = []
        frame = frames[thread.ident] if thread.ident in frames else None
        while frame is not None:
            stack_frames.append(StackFrame(
                methodName=frame.f_code.co_name,
                fileName=Path(frame.f_code.co_filename).name,
                lineNumber=frame.f_lineno,
                className=guess_class_name(),
                nativeMethod=False
            ))
            frame = frame.f_back  # move one frame back
        return stack_frames

    def _calc_thread_state(self, thread: threading.Thread) -> str:
        if thread.ident and thread.ident < 0:
            return "NEW"
        return "RUNNABLE"
