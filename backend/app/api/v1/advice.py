"""LLM 달리기 조언 엔드포인트 (SSE 스트리밍)."""

import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import Activity
from app.models.lap import Lap
from app.models.llm_advice import LLMAdvice
from app.models.user import User
from app.schemas.advice import AdviceHistoryResponse, AdviceHistoryItem
from app.services.llm import get_llm_client

router = APIRouter(prefix="/advice", tags=["advice"])

_SYSTEM_PROMPT = """당신은 전문 달리기 코치입니다.
사용자의 운동 데이터를 분석하고, 구체적이고 실용적인 훈련 조언을 한국어로 제공합니다.
데이터에 근거한 조언을 하되, 이해하기 쉽고 동기부여가 되는 방식으로 설명하세요.
마크다운 형식으로 구조화하여 응답하세요."""


# ─────────────────────────────────────────────
# 컨텍스트 빌더
# ─────────────────────────────────────────────


def _format_pace(average_speed: float | None) -> str:
    if not average_speed or average_speed <= 0:
        return "-"
    sec = 1000 / average_speed
    return f"{int(sec // 60)}:{int(sec % 60):02d} /km"


def _format_time(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_activity_context(activity: Activity, laps: list[Lap]) -> str:
    lines = [
        f"날짜: {activity.start_date_local.strftime('%Y-%m-%d %H:%M')}",
        f"이름: {activity.name or '달리기'}",
        f"거리: {(activity.distance or 0) / 1000:.2f} km",
        f"운동 시간: {_format_time(activity.moving_time)}",
        f"평균 페이스: {_format_pace(activity.average_speed)}",
    ]
    if activity.average_heartrate:
        lines.append(f"평균 심박: {activity.average_heartrate:.0f} bpm")
    if activity.max_heartrate:
        lines.append(f"최대 심박: {activity.max_heartrate:.0f} bpm")
    if activity.total_elevation_gain:
        lines.append(f"누적 고도: {activity.total_elevation_gain:.0f} m")
    if activity.average_cadence:
        lines.append(f"평균 케이던스: {activity.average_cadence:.0f} spm")
    if activity.calories:
        lines.append(f"칼로리: {activity.calories:.0f} kcal")
    if activity.suffer_score:
        lines.append(f"고통 점수: {activity.suffer_score}")

    if laps:
        lines.append(f"\n랩 데이터 ({min(len(laps), 20)}개):")
        lines.append("| 랩 | 거리 | 페이스 | 심박 |")
        lines.append("|----|------|--------|------|")
        for lap in laps[:20]:
            dist = f"{(lap.distance or 0) / 1000:.2f} km"
            pace = _format_pace(lap.average_speed)
            hr = f"{lap.average_heartrate:.0f}" if lap.average_heartrate else "-"
            lines.append(f"| {lap.lap_index} | {dist} | {pace} | {hr} |")

    return "\n".join(lines)


def _build_general_context(activities: list[Activity]) -> str:
    if not activities:
        return "최근 4주간 기록 없음"

    total_dist = sum((a.distance or 0) for a in activities) / 1000
    total_time = sum((a.moving_time or 0) for a in activities)
    avg_pace_list = [a.average_speed for a in activities if a.average_speed]
    avg_pace = _format_pace(sum(avg_pace_list) / len(avg_pace_list)) if avg_pace_list else "-"

    lines = [
        f"## 최근 4주 요약",
        f"- 총 활동 수: {len(activities)}회",
        f"- 총 거리: {total_dist:.1f} km",
        f"- 총 운동 시간: {_format_time(total_time)}",
        f"- 평균 페이스: {avg_pace}",
        "",
        "## 활동별 상세",
    ]
    for a in activities[:10]:
        date = a.start_date_local.strftime("%m/%d")
        dist = f"{(a.distance or 0) / 1000:.1f}km"
        pace = _format_pace(a.average_speed)
        lines.append(f"- {date} | {dist} | {pace}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# SSE 스트림 생성기
# ─────────────────────────────────────────────


async def _stream_advice(
    prompt_context: str,
    user_prompt: str,
    user_id: int,
    activity_id: int | None,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """LLM에서 텍스트를 스트리밍하고, 완료 후 DB에 저장한다."""
    llm = get_llm_client()
    full_response = []

    try:
        async for token in llm.stream_completion(system=_SYSTEM_PROMPT, user=user_prompt):
            full_response.append(token)
            yield f"data: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"
    finally:
        response_text = "".join(full_response)
        if response_text:
            advice = LLMAdvice(
                user_id=user_id,
                activity_id=activity_id,
                prompt_context=prompt_context,
                response_text=response_text,
                model_used=f"{llm.__class__.__name__}",
            )
            db.add(advice)
            await db.commit()

    yield "data: [DONE]\n\n"


# ─────────────────────────────────────────────
# 엔드포인트
# ─────────────────────────────────────────────


@router.post("/activity/{activity_id}")
async def advice_for_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """특정 활동에 대한 AI 조언을 SSE로 스트리밍한다."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Activity)
        .where(Activity.id == activity_id, Activity.user_id == current_user.id)
        .options(selectinload(Activity.laps))
    )
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    context = _build_activity_context(activity, activity.laps)
    user_prompt = f"다음 달리기 활동을 분석하고 개선을 위한 구체적인 조언을 해주세요:\n\n{context}"

    return StreamingResponse(
        _stream_advice(context, user_prompt, current_user.id, activity_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/general")
async def advice_general(
    weeks: int = Query(4, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """최근 N주 활동 기반 종합 조언을 SSE로 스트리밍한다."""
    since = datetime.now(tz=timezone.utc) - timedelta(weeks=weeks)
    result = await db.execute(
        select(Activity)
        .where(Activity.user_id == current_user.id, Activity.start_date >= since)
        .order_by(Activity.start_date.desc())
        .limit(30)
    )
    activities = list(result.scalars().all())

    context = _build_general_context(activities)
    user_prompt = (
        f"다음은 최근 {weeks}주간의 달리기 기록입니다. "
        f"전반적인 훈련 패턴을 분석하고 종합적인 개선 조언을 해주세요:\n\n{context}"
    )

    return StreamingResponse(
        _stream_advice(context, user_prompt, current_user.id, None, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=AdviceHistoryResponse)
async def advice_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdviceHistoryResponse:
    """사용자의 과거 AI 조언 목록을 반환한다."""
    base = select(LLMAdvice).where(LLMAdvice.user_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(LLMAdvice.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = result.scalars().all()
    return AdviceHistoryResponse(
        items=[AdviceHistoryItem.model_validate(i) for i in items],
        total=total or 0,
    )
