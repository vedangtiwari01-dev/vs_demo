"""
Clean and concise logger with aggregation support
Provides readable, summarized output with minimal noise
"""

import os
import time
from typing import Dict, Any, Optional
from collections import Counter


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'


class CleanLogger:
    """Clean, aggregated logger for AI service"""

    def __init__(self):
        self.is_verbose = os.getenv('LOG_VERBOSE', 'false').lower() == 'true'

    def _color(self, text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{Colors.RESET}"

    def endpoint(self, method: str, path: str, meta: Optional[Dict[str, Any]] = None):
        """Log an API endpoint call"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"\n{self._color('►', Colors.CYAN)} {self._color(Colors.BOLD + method + Colors.RESET, Colors.WHITE)} {path} {self._color(f'[{timestamp}]', Colors.GRAY)}")

        if meta:
            for key, value in meta.items():
                print(f"  {self._color('│', Colors.GRAY)} {key}: {self._color(str(value), Colors.WHITE)}")

    def step(self, step_name: str, details: Optional[Dict[str, Any]] = None):
        """Log a processing step"""
        print(f"  {self._color('●', Colors.BLUE)} {self._color(Colors.BOLD + step_name + Colors.RESET, Colors.WHITE)}")

        if details:
            for key, value in details.items():
                print(f"    {self._color('•', Colors.GRAY)} {key}: {self._color(str(value), Colors.WHITE)}")

    def success(self, message: str, summary: Optional[Dict[str, Any]] = None):
        """Log a success result"""
        print(f"  {self._color('✓', Colors.GREEN)} {self._color(Colors.BOLD + message + Colors.RESET, Colors.GREEN)}")

        if summary:
            for key, value in summary.items():
                print(f"    {self._color('•', Colors.GRAY)} {key}: {self._color(str(value), Colors.GREEN)}")

    def error(self, message: str, error: Optional[Exception] = None):
        """Log an error"""
        print(f"  {self._color('✗', Colors.RED)} {self._color(Colors.BOLD + message + Colors.RESET, Colors.RED)}")

        if error and self.is_verbose:
            print(f"    {self._color('•', Colors.GRAY)} {self._color(str(error), Colors.RED)}")

    def warn(self, message: str, details: Optional[str] = None):
        """Log a warning"""
        print(f"  {self._color('⚠', Colors.YELLOW)} {self._color(message, Colors.YELLOW)}")

        if details and self.is_verbose:
            print(f"    {self._color('•', Colors.GRAY)} {self._color(details, Colors.GRAY)}")

    def aggregated(self, title: str, items: Dict[str, int], show_total: bool = True, max_items: int = 10):
        """Log aggregated results with visual bars"""
        print(f"\n  {self._color('◆', Colors.CYAN)} {self._color(Colors.BOLD + title + Colors.RESET, Colors.WHITE)}")

        entries = list(items.items())
        total = sum(count for _, count in entries if isinstance(count, int))

        # Sort by count (descending) and limit
        sorted_entries = sorted(entries, key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True)[:max_items]

        for key, value in sorted_entries:
            bar = self._create_bar(value, total)
            print(f"    {self._color('│', Colors.GRAY)} {self._color(str(key).ljust(30), Colors.WHITE)} {self._color(str(value), Colors.CYAN)} {bar}")

        if len(entries) > max_items:
            print(f"    {self._color('│', Colors.GRAY)} {self._color(f'... and {len(entries) - max_items} more', Colors.GRAY)}")

        if show_total and len(entries) > 1:
            print(f"    {self._color('│', Colors.GRAY)} {self._color(Colors.BOLD + 'TOTAL'.ljust(30) + Colors.RESET, Colors.WHITE)} {self._color(Colors.BOLD + str(total) + Colors.RESET, Colors.CYAN)}")

    def _create_bar(self, value: int, total: int, max_width: int = 15) -> str:
        """Create a text-based progress bar"""
        if not total or total == 0:
            return ''

        percentage = min(value / total, 1.0)
        filled = round(percentage * max_width)
        empty = max_width - filled

        return (self._color('[', Colors.GRAY) +
                self._color('█' * filled, Colors.CYAN) +
                self._color('░' * empty, Colors.GRAY) +
                self._color(']', Colors.GRAY))

    def debug(self, message: str, data: Any = None):
        """Log debug information (only if LOG_VERBOSE=true)"""
        if not self.is_verbose:
            return

        print(f"  {self._color('◯', Colors.GRAY)} {self._color(message, Colors.GRAY)}")
        if data:
            print(f"    {self._color(str(data), Colors.GRAY)}")

    def separator(self):
        """Log a separator line"""
        print(f"{self._color('─' * 60, Colors.GRAY)}")

    def start_timer(self) -> float:
        """Start timing an operation"""
        return time.time()

    def get_elapsed(self, start_time: float) -> str:
        """Get elapsed time in human-readable format"""
        elapsed = time.time() - start_time

        if elapsed < 1:
            return f"{int(elapsed * 1000)}ms"
        elif elapsed < 60:
            return f"{elapsed:.1f}s"
        else:
            minutes = int(elapsed / 60)
            seconds = int(elapsed % 60)
            return f"{minutes}m {seconds}s"


# Export singleton instance
clean_logger = CleanLogger()
