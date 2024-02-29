from datetime import datetime

from alembic_utils.pg_function import PGFunction
from sqlalchemy import Float, Integer, String, column, func

freeze_time = PGFunction(
    schema="public",
    signature="freeze_time(freeze_time timestamp with time zone, tick bool default false)",
    definition="""
    RETURNS void AS
    $$
    BEGIN
        insert into freeze_time_params(param, value) values
            ('enabled', 'true'),
            ('timestamp',  EXTRACT(EPOCH FROM freeze_time)::text::jsonb),
            ('tick', tick::text::jsonb)
        on conflict(param) do update set
            value = excluded.value;
    END
    $$ language plpgsql;
    """,
)
unfreeze_time = PGFunction(
    schema="public",
    signature="unfreeze_time()",
    definition="""
    RETURNS void AS
    $$
    BEGIN
        insert into freeze_time_params(param, value) values
            ('enabled', 'false')
        on conflict(param) do update set
            value = excluded.value;
    END
    $$ language plpgsql;
    """,
)

freezable_now = PGFunction(
    schema="public",
    signature="freezable_now()",
    definition="""
    RETURNS timestamptz AS
    $$
    DECLARE enabled text;
    DECLARE tick text;
    DECLARE timestamp timestamp;
    BEGIN
        select into enabled value from freeze_time_params where param = 'enabled';
        select into tick value from freeze_time_params where param = 'tick';
    
        if enabled then
            select into timestamp to_timestamp(value::text::decimal) from freeze_time_params where param = 'timestamp';
    
            if tick then
                timestamp = timestamp + '1 second'::interval;
                update freeze_time_params set value = extract(epoch from timestamp)::text::jsonb where param = 'timestamp';
            end if;
    
            return timestamp;
        else
            return pg_catalog.now();
    
        end if;
    END
    $$ language plpgsql;
    """,
)

__consumed_by_customer__ = PGFunction(
    schema="public",
    signature="consumed_by_customer(customer varchar, account_start timestamp, account_stop timestamp)",
    definition="""
    RETURNS TABLE (owner varchar, count bigint, hours numeric, seconds bigint)
    AS $$
        SELECT
            campaign.owner,
            count(*),
            round(
                sum(
                    extract(
                        'epoch' FROM (
                            least(coalesce(account_stop, freezable_now()::timestamp), stopped_at) - greatest(account_start, started_at)
                        )
                    ) / 3600 * cp.num_cores
                )::numeric,
                2
            ) AS hours,
            round(
                sum(
                    extract(
                        'epoch' FROM (
                            least(coalesce(account_stop, freezable_now()::timestamp), stopped_at) - greatest(account_start, started_at)
                        )
                    ) * cp.num_cores
                )
            )::bigint AS seconds
        FROM campaign
        JOIN campaign_parameters cp on campaign.id = cp.campaign_id
        WHERE started_at <= coalesce(account_stop, freezable_now()::timestamp)
        AND (stopped_at IS NULL OR stopped_at >= account_start)
        AND (status in ('RUNNING', 'STOPPED'))
        AND campaign.owner = customer
        GROUP BY campaign.owner;
    $$
    LANGUAGE SQL;
    """,
)


def consumed_by_customer(
    owner: str, started_at: datetime, stopped_at: datetime = datetime.utcnow()
):
    return func.consumed_by_customer(owner, started_at, stopped_at).table_valued(
        column("owner", String),
        column("count", Integer),
        column("hours", Float),
        column("seconds", Integer),
    )
