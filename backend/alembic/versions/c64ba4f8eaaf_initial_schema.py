"""initial_schema

Revision ID: c64ba4f8eaaf
Revises:
Create Date: 2026-04-12 09:54:56.341119

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c64ba4f8eaaf"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users (Google 기반 인증) ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_id", sa.String(100), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("picture", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- data_sources (공급자별 OAuth 토큰 — 현재: strava) ---
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),       # "strava" | ...
        sa.Column("external_id", sa.String(100), nullable=False),   # 공급자 측 사용자 ID
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_data_sources_user_provider", "data_sources", ["user_id", "provider"]
    )
    op.create_index("idx_data_sources_user_id", "data_sources", ["user_id"])

    # --- activities ---
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strava_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("type", sa.String(50)),
        sa.Column("sport_type", sa.String(50)),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_date_local", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(100)),
        sa.Column("distance", sa.Float()),
        sa.Column("moving_time", sa.Integer()),
        sa.Column("elapsed_time", sa.Integer()),
        sa.Column("total_elevation_gain", sa.Float()),
        sa.Column("average_speed", sa.Float()),
        sa.Column("max_speed", sa.Float()),
        sa.Column("average_cadence", sa.Float()),
        sa.Column("average_heartrate", sa.Float()),
        sa.Column("max_heartrate", sa.Float()),
        sa.Column("calories", sa.Float()),
        sa.Column("suffer_score", sa.Integer()),
        sa.Column("summary_polyline", sa.Text()),
        sa.Column("map_id", sa.String(100)),
        sa.Column("achievement_count", sa.Integer(), server_default="0"),
        sa.Column("kudos_count", sa.Integer(), server_default="0"),
        sa.Column("pr_count", sa.Integer(), server_default="0"),
        sa.Column("trainer", sa.Boolean(), server_default="false"),
        sa.Column("commute", sa.Boolean(), server_default="false"),
        sa.Column("manual", sa.Boolean(), server_default="false"),
        sa.Column("raw_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_activities_user_id", "activities", ["user_id"])
    op.create_index("idx_activities_start_date", "activities", ["start_date"])

    # --- laps ---
    op.create_table(
        "laps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strava_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lap_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("elapsed_time", sa.Integer()),
        sa.Column("moving_time", sa.Integer()),
        sa.Column("distance", sa.Float()),
        sa.Column("average_speed", sa.Float()),
        sa.Column("max_speed", sa.Float()),
        sa.Column("average_cadence", sa.Float()),
        sa.Column("average_heartrate", sa.Float()),
        sa.Column("max_heartrate", sa.Float()),
        sa.Column("total_elevation_gain", sa.Float()),
        sa.Column("pace_zone", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_laps_activity_id", "laps", ["activity_id"])

    # --- llm_advices ---
    op.create_table(
        "llm_advices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL")),
        sa.Column("prompt_context", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("llm_advices")
    op.drop_index("idx_laps_activity_id", "laps")
    op.drop_table("laps")
    op.drop_index("idx_activities_start_date", "activities")
    op.drop_index("idx_activities_user_id", "activities")
    op.drop_table("activities")
    op.drop_index("idx_data_sources_user_id", "data_sources")
    op.drop_constraint("uq_data_sources_user_provider", "data_sources")
    op.drop_table("data_sources")
    op.drop_table("users")
