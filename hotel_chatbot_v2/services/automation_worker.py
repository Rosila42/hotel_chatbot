from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from hotel_chatbot_v2.services.automation_service import AutomationService


class AutomationWorker:
    def __init__(self, service: AutomationService) -> None:
        self.service = service
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def schedule_morning_arrival_check(self, hour: int = 8, minute: int = 0) -> None:
        self.scheduler.add_job(
            self._run_morning_arrival_check,
            trigger="cron",
            hour=hour,
            minute=minute,
            id="morning-arrival-check",
            replace_existing=True,
        )

    def _run_morning_arrival_check(self) -> dict:
        return self.service.run("MORNING_ARRIVAL_CHECK")
