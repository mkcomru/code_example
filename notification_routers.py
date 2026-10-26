from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from tortoise.exceptions import DoesNotExist

from src.backend.modules.auth.dependencies import (
    CurrentUserDep,
    require_company_viewer,
)
from src.backend.modules.notifications.dependencies import NotificationServiceDep
from src.backend.modules.notifications.notification_schemas import (
    CompanyNotificationSummary,
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationRecipientResponse,
    UnreadCountResponse,
)
from src.backend.modules.users.models import CompanyUser

company_router = APIRouter(prefix="/companies/{company_id}/notifications", tags=["notifications"])
user_router = APIRouter(prefix="/notifications", tags=["notifications"])


@company_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    notification_svc: NotificationServiceDep,
    company_id: int = Path(..., ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    current_user: CompanyUser = Depends(require_company_viewer),
) -> NotificationListResponse:
    repo = notification_svc.repo
    recipients = await repo.list_for_user(
        company_user_id=current_user.id,
        company_id=company_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    total = await repo.count_for_user(current_user.id, company_id, unread_only=unread_only)
    unread_count = await repo.unread_count(current_user.id, company_id)
    return NotificationListResponse(
        items=[NotificationRecipientResponse.from_model(r) for r in recipients],
        total=total,
        unread_count=unread_count,
    )


@company_router.post("/{recipient_id}/read", response_model=NotificationRecipientResponse)
async def mark_notification_read(
    notification_svc: NotificationServiceDep,
    company_id: int = Path(..., ge=1),
    recipient_id: int = Path(..., ge=1),
    current_user: CompanyUser = Depends(require_company_viewer),
) -> NotificationRecipientResponse:
    repo = notification_svc.repo
    try:
        recipient = await repo.mark_read(recipient_id=recipient_id, company_user_id=current_user.id)
    except DoesNotExist as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification recipient not found") from exc
    await recipient.fetch_related("notification")
    return NotificationRecipientResponse.from_model(recipient)


@company_router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    notification_svc: NotificationServiceDep,
    company_id: int = Path(..., ge=1),
    current_user: CompanyUser = Depends(require_company_viewer),
) -> MarkAllReadResponse:
    repo = notification_svc.repo
    updated = await repo.mark_all_read(company_user_id=current_user.id, company_id=company_id)
    return MarkAllReadResponse(updated=updated)


@company_router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    notification_svc: NotificationServiceDep,
    company_id: int = Path(..., ge=1),
    current_user: CompanyUser = Depends(require_company_viewer),
) -> UnreadCountResponse:
    repo = notification_svc.repo
    count = await repo.unread_count(company_user_id=current_user.id, company_id=company_id)
    return UnreadCountResponse(count=count)


@user_router.get("/summary", response_model=list[CompanyNotificationSummary])
async def notifications_summary(
    notification_svc: NotificationServiceDep,
    current_user: CurrentUserDep,
) -> list[CompanyNotificationSummary]:
    company_users = await CompanyUser.filter(user_id=current_user.id)
    if not company_users:
        return []
    repo = notification_svc.repo
    counts = await repo.unread_counts_by_company([cu.id for cu in company_users])
    return [
        CompanyNotificationSummary(company_id=cu.company_id, unread_count=counts.get(cu.id, 0)) for cu in company_users
    ]
