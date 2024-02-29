from alembic_utils.pg_view import PGView
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from .base import Base

__CampaignAggregatedView__ = PGView(
    schema="public",
    signature="campaign_aggregated_view",
    definition="""
SELECT
    md5(random()::text || clock_timestamp()::text)::uuid AS uid,
    GROUPING(cmp.id) as group_by_id,
    GROUPING(cmp.name) as group_by_name,
    cmp.owner,
    month,
    year,
    count(*),
    round(sum(extract('epoch' FROM (end_date_2 - start_date_2)) * cp.num_cores))::bigint AS seconds,
    sum(extract('epoch' FROM (end_date_2 - start_date_2)) / 60 * cp.num_cores)::numeric AS minutes,
    round(sum(extract('epoch' FROM (end_date_2 - start_date_2)) / 3600 * cp.num_cores)::numeric, 2) AS hours,
    cmp.id,
    cmp.name,
    cmp.started_at,
    cmp.stopped_at
    FROM campaign AS cmp
    JOIN campaign_parameters AS cp ON cmp.id = cp.campaign_id
    LEFT JOIN LATERAL (
        SELECT
            least(
                (date_trunc('month', generate_series) + interval '1 month - 1 microsecond'),
                coalesce(cmp.stopped_at, freezable_now())
            ) as end_date_2,
            greatest(date_trunc('month', generate_series), cmp.started_at) as start_date_2,
            extract(MONTH FROM generate_series) as month,
            extract(YEAR FROM generate_series)  as year
        FROM
            -- +1 month here to cover intervals <= 1 month and when campaign's started_at and stopped_at at different months
            generate_series(cmp.started_at, coalesce(cmp.stopped_at, freezable_now()) + interval '1 month', '1 month')
        -- for cases when a generated start date (+1 month to campaign.stopped_at) is greater than campaign.stopped_at
        WHERE date_trunc('month', generate_series) <= coalesce(cmp.stopped_at, freezable_now())
    ) e1 ON start_date_2 <= end_date_2 -- for cases when campaign was started later than now
    WHERE cmp.status IN ('RUNNING', 'STOPPED')
    GROUP BY
        GROUPING SETS (
            -- for an aggregated run time at each month detailed by each campaign's run time (group_by_id=0 && group_by_name=0)
            (cmp.owner, month, year, (cmp.id, cmp.name, cmp.started_at, cmp.stopped_at, start_date_2, end_date_2)),
            -- for an aggregated run time at each month (group_by_id=1 && group_by_name=1)
            (cmp.owner, month, year),
            -- for a single campaign run time calculation (group_by_id=0 && group_by_name=1)
            (cmp.owner, cmp.id)
        );
    """,
)

__OwnerAggregatedView__ = PGView(
    schema="public",
    signature="owner_aggregated_view",
    definition="""
SELECT
    md5(owner || extract(MONTH FROM account_start)::text || extract(YEAR FROM account_start)::text)::uuid as uid,
    owner,
    extract(MONTH FROM account_start) as month,
    extract(YEAR FROM account_start) as year,
    seconds,
    round(seconds / 3600.0, 2) as hours
FROM (
  SELECT
    owner,
    date_trunc('month', min(cmp1.started_at)) as ss,
    date_trunc('month', max(coalesce(cmp1.stopped_at, freezable_now()::timestamp))) as ee
  FROM campaign as cmp1
  WHERE cmp1.status IN ('RUNNING', 'STOPPED')
  GROUP BY owner
) e1
JOIN LATERAL (
    SELECT
      generate_series as account_start,
      least(generate_series + interval '1 month - 1 microsecond', freezable_now()::timestamp) as account_stop
    FROM generate_series(ss, ee + '1 month'::interval, '1 month')
    WHERE generate_series <= ee
) e2 ON TRUE
JOIN LATERAL (
    SELECT coalesce(round(sum(extract('epoch' FROM (
        least(coalesce(cmp.stopped_at, freezable_now()::timestamp), account_stop) - greatest(cmp.started_at, account_start)
        )) * cp.num_cores)), 0)::bigint AS seconds
    FROM campaign as cmp
    JOIN campaign_parameters cp on cmp.id = cp.campaign_id
    WHERE cmp.started_at <= account_stop
    AND (
        cmp.stopped_at >= account_start
        OR cmp.stopped_at IS NULL
    )
    AND cmp.status IN ('RUNNING', 'STOPPED')
    AND cmp.owner = e1.owner
) e3 ON TRUE
;
    """,
)


__CustomersWithLimitsView__ = PGView(
    schema="public",
    signature="owner_limits_view",
    definition="""
SELECT
    md5(owner)::uuid as uid,
    owner,
    stripe_customer_id,
    fuzzing_limit
FROM (
    SELECT owner
    FROM campaign
    WHERE status='RUNNING'
    GROUP BY owner
) t1 JOIN LATERAL (
    SELECT fuzzing_limit, stripe_customer_id
    FROM customer
    WHERE customer.user_id = owner
) t2 ON fuzzing_limit IS NOT NULL;
    """,
)

__FullCampaignView__ = PGView(
    schema="public",
    signature="full_campaign_view",
    definition="""
    SELECT
        cmp.id,
        cmp.owner,
        cmp.name,
        cmp.project,
        cmp.num_sources,
        cmp.corpus_target,
        cmp.status,
        cmp.submitted_at,
        cmp.started_at,
        cmp.stopped_at,
        cmp.error,
        cmp.public,
        cmp.deleted,
        prj.name as project_name,
        report.run_time,
        report.vulnerabilities_high,
        report.vulnerabilities_medium,
        report.vulnerabilities_low,
        report.vulnerabilities_none,
        cp.time_limit
    FROM campaign as cmp
    LEFT JOIN project prj ON cmp.project = prj.id
    LEFT JOIN campaign_parameters cp ON cmp.id = cp.campaign_id
    LEFT JOIN report ON cmp.id = report.campaign_id;
    """,
)


class CampaignAggregatedView(Base):
    __tablename__ = "campaign_aggregated_view"
    __table_args__ = {"info": {"is_view": True}}  # used in migrations/env.py

    uid = Column(String, primary_key=True)
    group_by_id = Column(Integer, nullable=False)
    group_by_name = Column(Integer, nullable=False)
    owner = Column(String, nullable=False)
    month = Column(Integer)
    year = Column(Integer)
    count = Column(Integer, nullable=False)
    seconds = Column(Integer, nullable=False)
    minutes = Column(Float, nullable=False)
    hours = Column(Float, nullable=False)
    id = Column(String)
    name = Column(String)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)


class OwnerAggregatedView(Base):
    __tablename__ = "owner_aggregated_view"
    __table_args__ = {"info": {"is_view": True}}  # used in migrations/env.py

    uid = Column(String, primary_key=True)
    owner = Column(String, nullable=False)
    month = Column(Integer)
    year = Column(Integer)
    seconds = Column(Integer, nullable=False)
    hours = Column(Float, nullable=False)


class CustomersWithLimitsView(Base):
    __tablename__ = "owner_limits_view"
    __table_args__ = {"info": {"is_view": True}}  # used in migrations/env.py

    uid = Column(String, primary_key=True)
    owner = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=False)
    fuzzing_limit = Column(Integer, nullable=False)


class FullCampaignView(Base):
    __tablename__ = "full_campaign_view"
    __table_args__ = {"info": {"is_view": True}}  # used in migrations/env.py
    id = Column(String, primary_key=True)
    name = Column(String)
    project = Column(String)
    project_name = Column(String, nullable=False)
    corpus_target = Column(String)
    num_sources = Column(Integer, nullable=False)
    status = Column(String)
    submitted_at = Column(DateTime)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    error = Column(String)
    owner = Column(String)
    deleted = Column(Boolean, nullable=False)
    public = Column(Boolean, nullable=False)
    run_time = Column(Integer)
    vulnerabilities_high = Column(Integer)
    vulnerabilities_medium = Column(Integer)
    vulnerabilities_low = Column(Integer)
    vulnerabilities_none = Column(Integer)
    time_limit = Column(Integer)
