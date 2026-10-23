"""Domain decision for a weekly field-service follow-up digest."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field

DispatchStatus = Literal["scheduled", "dispatched", "in_progress", "completed", "cancelled"]


class WorkOrder(BaseModel):
    work_order_id: str
    customer_name: str
    technician_name: str
    dispatch_status: DispatchStatus
    photo_urls: list[str] = Field(default_factory=list)
    technician_follow_up: bool = False


class DigestRequest(BaseModel):
    audience: str
    week_ending: str
    work_orders: list[WorkOrder]


class FollowUpItem(BaseModel):
    work_order_id: str
    technician_name: str
    reason: Literal["missing_photos", "technician_flagged"]


class DigestResult(BaseModel):
    audience: str
    week_ending: str
    total_work_orders: int
    dispatch_counts: dict[str, int]
    photo_count: int
    follow_ups: list[FollowUpItem]


def build_weekly_digest(request: DigestRequest) -> DigestResult:
    """Select active jobs that need a concrete technician follow-up."""
    follow_ups: list[FollowUpItem] = []
    for order in request.work_orders:
        if order.dispatch_status not in {"dispatched", "in_progress"}:
            continue
        if order.technician_follow_up:
            reason = "technician_flagged"
        elif not order.photo_urls:
            reason = "missing_photos"
        else:
            continue
        follow_ups.append(
            FollowUpItem(
                work_order_id=order.work_order_id,
                technician_name=order.technician_name,
                reason=reason,
            )
        )

    return DigestResult(
        audience=request.audience,
        week_ending=request.week_ending,
        total_work_orders=len(request.work_orders),
        dispatch_counts=dict(Counter(order.dispatch_status for order in request.work_orders)),
        photo_count=sum(len(order.photo_urls) for order in request.work_orders),
        follow_ups=follow_ups,
    )
