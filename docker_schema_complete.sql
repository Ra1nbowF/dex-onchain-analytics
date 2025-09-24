--
-- PostgreSQL database dump
--

\restrict 0CaR58IbJqlwtDSaMgoDPjh1JdFLfV3WOH9Rq51LzRhHRlrc2kbl8m6zcXF8J9N

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: refresh_materialized_views(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_materialized_views() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_dex_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_pairs_24h;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bsc_liquidity_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bsc_liquidity_events (
    id integer NOT NULL,
    tx_hash character varying(66),
    event_type character varying(20),
    provider_address character varying(42),
    btcb_amount numeric(40,18),
    usdt_amount numeric(40,18),
    lp_tokens numeric(40,18),
    share_of_pool numeric(10,4),
    "timestamp" timestamp without time zone
);


--
-- Name: bsc_liquidity_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bsc_liquidity_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bsc_liquidity_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bsc_liquidity_events_id_seq OWNED BY public.bsc_liquidity_events.id;


--
-- Name: bsc_pool_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bsc_pool_metrics (
    id integer NOT NULL,
    pool_address character varying(42),
    token0_reserve numeric(40,18),
    token1_reserve numeric(40,18),
    total_liquidity_usd numeric(30,2),
    tvl numeric(30,2),
    price_btcb_usdt numeric(20,8),
    pool_ratio numeric(10,4),
    lp_token_supply numeric(40,18),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: bsc_pool_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bsc_pool_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bsc_pool_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bsc_pool_metrics_id_seq OWNED BY public.bsc_pool_metrics.id;


--
-- Name: bsc_trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bsc_trades (
    id integer NOT NULL,
    tx_hash character varying(66),
    block_number bigint,
    trader_address character varying(42),
    token_in character varying(42),
    token_out character varying(42),
    amount_in numeric(40,18),
    amount_out numeric(40,18),
    price numeric(20,8),
    value_usd numeric(30,2),
    gas_used bigint,
    slippage numeric(10,4),
    is_buy boolean,
    "timestamp" timestamp without time zone
);


--
-- Name: bsc_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bsc_trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bsc_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bsc_trades_id_seq OWNED BY public.bsc_trades.id;


--
-- Name: bsc_wallet_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bsc_wallet_metrics (
    id integer NOT NULL,
    wallet_address character varying(42),
    btcb_balance numeric(40,18),
    usdt_balance numeric(40,18),
    lp_token_balance numeric(40,18),
    total_trades integer DEFAULT 0,
    total_volume_usd numeric(30,2) DEFAULT 0,
    realized_pnl numeric(30,2) DEFAULT 0,
    unrealized_pnl numeric(30,2) DEFAULT 0,
    win_rate numeric(5,2),
    avg_trade_size numeric(30,2),
    first_seen timestamp without time zone,
    last_seen timestamp without time zone,
    is_mm_suspect boolean DEFAULT false,
    is_insider_suspect boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: bsc_wallet_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bsc_wallet_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bsc_wallet_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bsc_wallet_metrics_id_seq OWNED BY public.bsc_wallet_metrics.id;


--
-- Name: chain_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chain_stats (
    id integer NOT NULL,
    chain_name character varying(50) NOT NULL,
    chain_id integer NOT NULL,
    total_volume_24h numeric(30,2),
    total_transactions integer,
    active_wallets integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: chain_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chain_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chain_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chain_stats_id_seq OWNED BY public.chain_stats.id;


--
-- Name: dex_trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dex_trades (
    id integer NOT NULL,
    chain_id integer NOT NULL,
    chain_name character varying(50),
    dex_name character varying(50) NOT NULL,
    pair character varying(50) NOT NULL,
    token_in character varying(20),
    token_out character varying(20),
    amount_in numeric(30,8),
    amount_out numeric(30,8),
    price numeric(20,8),
    value_usd numeric(30,2),
    trader_address character varying(42),
    tx_hash character varying(66),
    gas_used integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: dex_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dex_trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dex_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dex_trades_id_seq OWNED BY public.dex_trades.id;


--
-- Name: hourly_dex_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.hourly_dex_stats AS
 SELECT date_trunc('hour'::text, dex_trades."timestamp") AS hour,
    dex_trades.chain_name,
    dex_trades.dex_name,
    count(*) AS trade_count,
    sum(dex_trades.value_usd) AS volume_usd,
    avg(dex_trades.gas_used) AS avg_gas,
    count(DISTINCT dex_trades.trader_address) AS unique_traders
   FROM public.dex_trades
  GROUP BY (date_trunc('hour'::text, dex_trades."timestamp")), dex_trades.chain_name, dex_trades.dex_name
  ORDER BY (date_trunc('hour'::text, dex_trades."timestamp")) DESC
  WITH NO DATA;


--
-- Name: liquidity_pools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidity_pools (
    id integer NOT NULL,
    chain_id integer NOT NULL,
    chain_name character varying(50),
    dex_name character varying(50) NOT NULL,
    pool_address character varying(42),
    token0_symbol character varying(20),
    token1_symbol character varying(20),
    token0_reserve numeric(30,8),
    token1_reserve numeric(30,8),
    total_liquidity_usd numeric(30,2),
    volume_24h numeric(30,2),
    fees_24h numeric(20,2),
    apy numeric(10,4),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: liquidity_pools_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.liquidity_pools_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: liquidity_pools_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.liquidity_pools_id_seq OWNED BY public.liquidity_pools.id;


--
-- Name: manipulation_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manipulation_alerts (
    id integer NOT NULL,
    alert_type character varying(50),
    severity character varying(20),
    description text,
    evidence jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: manipulation_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.manipulation_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: manipulation_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.manipulation_alerts_id_seq OWNED BY public.manipulation_alerts.id;


--
-- Name: market_manipulation_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.market_manipulation_alerts (
    id integer NOT NULL,
    alert_type character varying(50),
    severity character varying(20),
    pair_address character varying(42),
    description text,
    metrics jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: market_manipulation_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.market_manipulation_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: market_manipulation_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.market_manipulation_alerts_id_seq OWNED BY public.market_manipulation_alerts.id;


--
-- Name: moralis_historical_holders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_historical_holders (
    id integer NOT NULL,
    token_address character varying(42),
    holder_count integer,
    unique_wallets integer,
    data_timestamp timestamp without time zone,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_historical_holders_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_historical_holders_correct (
    id integer NOT NULL,
    token_address text,
    "timestamp" timestamp without time zone,
    total_holders integer,
    net_holder_change integer,
    holder_percent_change numeric(20,6),
    new_holders_by_swap integer,
    new_holders_by_transfer integer,
    new_holders_by_airdrop integer,
    holders_in_whales integer,
    holders_in_sharks integer,
    holders_in_dolphins integer,
    holders_in_fish integer,
    holders_in_octopus integer,
    holders_in_crabs integer,
    holders_in_shrimps integer,
    holders_out_whales integer,
    holders_out_sharks integer,
    holders_out_dolphins integer,
    holders_out_fish integer,
    holders_out_octopus integer,
    holders_out_crabs integer,
    holders_out_shrimps integer
);


--
-- Name: moralis_historical_holders_correct_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_historical_holders_correct_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_historical_holders_correct_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_historical_holders_correct_id_seq OWNED BY public.moralis_historical_holders_correct.id;


--
-- Name: moralis_historical_holders_enhanced; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_historical_holders_enhanced (
    id integer NOT NULL,
    token_address text,
    "timestamp" timestamp without time zone,
    total_holders integer,
    net_holder_change integer,
    holder_percent_change numeric(10,6),
    new_holders_by_swap integer,
    new_holders_by_transfer integer,
    new_holders_by_airdrop integer,
    holders_in_whales integer,
    holders_in_sharks integer,
    holders_in_dolphins integer,
    holders_in_fish integer,
    holders_in_octopus integer,
    holders_in_crabs integer,
    holders_in_shrimps integer,
    holders_out_whales integer,
    holders_out_sharks integer,
    holders_out_dolphins integer,
    holders_out_fish integer,
    holders_out_octopus integer,
    holders_out_crabs integer,
    holders_out_shrimps integer
);


--
-- Name: moralis_historical_holders_enhanced_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_historical_holders_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_historical_holders_enhanced_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_historical_holders_enhanced_id_seq OWNED BY public.moralis_historical_holders_enhanced.id;


--
-- Name: moralis_historical_holders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_historical_holders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_historical_holders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_historical_holders_id_seq OWNED BY public.moralis_historical_holders.id;


--
-- Name: moralis_holder_distribution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_holder_distribution (
    id integer NOT NULL,
    token_address character varying(42),
    holder_address character varying(42),
    balance numeric(40,18),
    balance_usd numeric(30,2),
    percentage_of_supply numeric(10,6),
    first_transaction timestamp without time zone,
    last_transaction timestamp without time zone,
    transaction_count integer,
    is_whale boolean DEFAULT false,
    is_active boolean DEFAULT true,
    holder_type character varying(50),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_holder_distribution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_holder_distribution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_holder_distribution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_holder_distribution_id_seq OWNED BY public.moralis_holder_distribution.id;


--
-- Name: moralis_holder_stats_complete; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_holder_stats_complete (
    id integer NOT NULL,
    token_address character varying(42),
    total_holders integer,
    holders_change_5m integer,
    holders_change_1h integer,
    holders_change_24h integer,
    holders_change_7d integer,
    holders_change_30d integer,
    holders_change_pct_24h numeric(10,4),
    holders_by_swap integer,
    holders_by_transfer integer,
    holders_by_airdrop integer,
    top_10_supply_pct numeric(10,4),
    top_25_supply_pct numeric(10,4),
    top_50_supply_pct numeric(10,4),
    top_100_supply_pct numeric(10,4),
    top_250_supply_pct numeric(10,4),
    top_500_supply_pct numeric(10,4),
    gini_coefficient numeric(10,6),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_holder_stats_complete_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_holder_stats_complete_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_holder_stats_complete_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_holder_stats_complete_id_seq OWNED BY public.moralis_holder_stats_complete.id;


--
-- Name: moralis_holder_stats_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_holder_stats_correct (
    id integer NOT NULL,
    token_address text,
    total_holders integer,
    top10_supply numeric(40,18),
    top10_supply_percent numeric(20,6),
    top25_supply numeric(40,18),
    top25_supply_percent numeric(20,6),
    top50_supply numeric(40,18),
    top50_supply_percent numeric(20,6),
    top100_supply numeric(40,18),
    top100_supply_percent numeric(20,6),
    top250_supply numeric(40,18),
    top250_supply_percent numeric(20,6),
    top500_supply numeric(40,18),
    top500_supply_percent numeric(20,6),
    holder_change_5min integer,
    holder_change_percent_5min numeric(20,6),
    holder_change_1h integer,
    holder_change_percent_1h numeric(20,6),
    holder_change_6h integer,
    holder_change_percent_6h numeric(20,6),
    holder_change_24h integer,
    holder_change_percent_24h numeric(20,6),
    holder_change_3d integer,
    holder_change_percent_3d numeric(20,6),
    holder_change_7d integer,
    holder_change_percent_7d numeric(20,6),
    holder_change_30d integer,
    holder_change_percent_30d numeric(20,6),
    holders_by_swap integer,
    holders_by_transfer integer,
    holders_by_airdrop integer,
    whales integer,
    sharks integer,
    dolphins integer,
    fish integer,
    octopus integer,
    crabs integer,
    shrimps integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_holder_stats_correct_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_holder_stats_correct_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_holder_stats_correct_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_holder_stats_correct_id_seq OWNED BY public.moralis_holder_stats_correct.id;


--
-- Name: moralis_holders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_holders (
    id integer NOT NULL,
    token_address text,
    holder_address text,
    balance numeric(40,18),
    balance_formatted numeric(20,8),
    percentage_of_supply numeric(10,6),
    holder_type text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_holders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_holders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_holders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_holders_id_seq OWNED BY public.moralis_holders.id;


--
-- Name: moralis_liquidity_changes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_liquidity_changes (
    id integer NOT NULL,
    pair_address character varying(42),
    event_type character varying(20),
    transaction_hash character varying(66),
    block_timestamp timestamp without time zone,
    wallet_address character varying(42),
    token0_amount numeric(40,18),
    token1_amount numeric(40,18),
    liquidity_change_usd numeric(30,2),
    total_liquidity_after numeric(30,2),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_liquidity_changes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_liquidity_changes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_liquidity_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_liquidity_changes_id_seq OWNED BY public.moralis_liquidity_changes.id;


--
-- Name: moralis_metrics_summary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_metrics_summary (
    id integer NOT NULL,
    token_address character varying(42),
    metric_type character varying(50),
    metric_value numeric(30,10),
    metric_json jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_metrics_summary_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_metrics_summary_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_metrics_summary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_metrics_summary_id_seq OWNED BY public.moralis_metrics_summary.id;


--
-- Name: moralis_pair_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_pair_stats (
    id integer NOT NULL,
    pair_address character varying(42),
    token_address character varying(42),
    exchange_address character varying(42),
    usd_price numeric(30,10),
    liquidity_usd numeric(30,2),
    price_change_5m numeric(10,4),
    price_change_1h numeric(10,4),
    price_change_24h numeric(10,4),
    liquidity_change_24h numeric(10,4),
    volume_24h numeric(30,2),
    buys_5m integer,
    sells_5m integer,
    buys_1h integer,
    sells_1h integer,
    buys_24h integer,
    sells_24h integer,
    buyers_1h integer,
    sellers_1h integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_pair_stats_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_pair_stats_correct (
    id integer NOT NULL,
    pair_address text,
    pair_label text,
    pair_created timestamp without time zone,
    token_address text,
    token_name text,
    token_symbol text,
    token_logo text,
    exchange text,
    exchange_address text,
    exchange_logo text,
    exchange_url text,
    current_usd_price numeric(40,18),
    current_native_price numeric(40,18),
    total_liquidity_usd numeric(40,18),
    price_change_5min numeric(20,6),
    price_change_1h numeric(20,6),
    price_change_4h numeric(20,6),
    price_change_24h numeric(20,6),
    liquidity_change_5min numeric(20,6),
    liquidity_change_1h numeric(20,6),
    liquidity_change_4h numeric(20,6),
    liquidity_change_24h numeric(20,6),
    buys_5min integer,
    buys_1h integer,
    buys_4h integer,
    buys_24h integer,
    sells_5min integer,
    sells_1h integer,
    sells_4h integer,
    sells_24h integer,
    total_volume_5min numeric(40,18),
    total_volume_1h numeric(40,18),
    total_volume_4h numeric(40,18),
    total_volume_24h numeric(40,18),
    buy_volume_5min numeric(40,18),
    buy_volume_1h numeric(40,18),
    buy_volume_4h numeric(40,18),
    buy_volume_24h numeric(40,18),
    sell_volume_5min numeric(40,18),
    sell_volume_1h numeric(40,18),
    sell_volume_4h numeric(40,18),
    sell_volume_24h numeric(40,18),
    buyers_5min integer,
    buyers_1h integer,
    buyers_4h integer,
    buyers_24h integer,
    sellers_5min integer,
    sellers_1h integer,
    sellers_4h integer,
    sellers_24h integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_pair_stats_correct_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_pair_stats_correct_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_pair_stats_correct_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_pair_stats_correct_id_seq OWNED BY public.moralis_pair_stats_correct.id;


--
-- Name: moralis_pair_stats_enhanced; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_pair_stats_enhanced (
    id integer NOT NULL,
    pair_address text,
    token_address text,
    token_name text,
    token_symbol text,
    token_logo text,
    pair_created timestamp without time zone,
    pair_label text,
    exchange text,
    exchange_address text,
    exchange_logo text,
    exchange_url text,
    current_usd_price numeric(20,10),
    current_native_price numeric(20,10),
    total_liquidity_usd numeric(20,2),
    price_change_5min numeric(10,6),
    price_change_1h numeric(10,6),
    price_change_4h numeric(10,6),
    price_change_24h numeric(10,6),
    liquidity_change_5min numeric(10,6),
    liquidity_change_1h numeric(10,6),
    liquidity_change_4h numeric(10,6),
    liquidity_change_24h numeric(10,6),
    buys_5min integer,
    buys_1h integer,
    buys_4h integer,
    buys_24h integer,
    sells_5min integer,
    sells_1h integer,
    sells_4h integer,
    sells_24h integer,
    volume_5min numeric(20,2),
    volume_1h numeric(20,2),
    volume_4h numeric(20,2),
    volume_24h numeric(20,2),
    buy_volume_5min numeric(20,2),
    buy_volume_1h numeric(20,2),
    buy_volume_4h numeric(20,2),
    buy_volume_24h numeric(20,2),
    sell_volume_5min numeric(20,2),
    sell_volume_1h numeric(20,2),
    sell_volume_4h numeric(20,2),
    sell_volume_24h numeric(20,2),
    buyers_5min integer,
    buyers_1h integer,
    buyers_4h integer,
    buyers_24h integer,
    sellers_5min integer,
    sellers_1h integer,
    sellers_4h integer,
    sellers_24h integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_pair_stats_enhanced_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_pair_stats_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_pair_stats_enhanced_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_pair_stats_enhanced_id_seq OWNED BY public.moralis_pair_stats_enhanced.id;


--
-- Name: moralis_pair_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_pair_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_pair_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_pair_stats_id_seq OWNED BY public.moralis_pair_stats.id;


--
-- Name: moralis_snipers_complete; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_snipers_complete (
    id integer NOT NULL,
    wallet_address character varying(42),
    pair_address character varying(42),
    tokens_bought numeric(40,18),
    tokens_sold numeric(40,18),
    buy_tx_hash character varying(66),
    sell_tx_hash character varying(66),
    buy_timestamp timestamp without time zone,
    sell_timestamp timestamp without time zone,
    buy_block integer,
    sell_block integer,
    blocks_held integer,
    time_held_seconds integer,
    realized_profit numeric(30,2),
    realized_profit_pct numeric(20,4),
    current_balance numeric(40,18),
    is_sniper boolean DEFAULT true,
    sniper_score numeric(5,2),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_snipers_complete_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_snipers_complete_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_snipers_complete_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_snipers_complete_id_seq OWNED BY public.moralis_snipers_complete.id;


--
-- Name: moralis_snipers_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_snipers_correct (
    id integer NOT NULL,
    pair_address text,
    wallet_address text,
    total_tokens_sniped numeric(40,18),
    total_sniped_usd numeric(40,18),
    total_sniped_transactions integer,
    total_tokens_sold numeric(40,18),
    total_sold_usd numeric(40,18),
    total_sell_transactions integer,
    current_balance numeric(40,18),
    current_balance_usd_value numeric(40,18),
    realized_profit_percentage numeric(20,6),
    realized_profit_usd numeric(40,18),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_snipers_correct_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_snipers_correct_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_snipers_correct_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_snipers_correct_id_seq OWNED BY public.moralis_snipers_correct.id;


--
-- Name: moralis_snipers_enhanced; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_snipers_enhanced (
    id integer NOT NULL,
    pair_address text,
    transaction_hash text,
    block_timestamp timestamp without time zone,
    block_number bigint,
    wallet_address text,
    total_tokens_sniped numeric(40,18),
    total_sniped_usd numeric(20,2),
    total_sniped_transactions integer,
    total_tokens_sold numeric(40,18),
    total_sold_usd numeric(20,2),
    total_sell_transactions integer,
    current_balance numeric(40,18),
    current_balance_usd_value numeric(20,2),
    realized_profit_percentage numeric(10,6),
    realized_profit_usd numeric(20,2),
    blocks_after_creation integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_snipers_enhanced_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_snipers_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_snipers_enhanced_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_snipers_enhanced_id_seq OWNED BY public.moralis_snipers_enhanced.id;


--
-- Name: moralis_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_stats (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    total_holders integer,
    unique_wallets integer,
    total_volume_24h numeric(20,2),
    total_transactions_24h integer,
    buy_volume_24h numeric(20,2),
    sell_volume_24h numeric(20,2),
    unique_buyers_24h integer,
    unique_sellers_24h integer,
    price_usd numeric(20,8),
    market_cap numeric(20,2),
    fully_diluted_valuation numeric(20,2),
    total_supply numeric(40,18),
    circulating_supply numeric(40,18),
    gini_coefficient numeric(5,4),
    top10_concentration numeric(10,6),
    top100_concentration numeric(10,6),
    whale_count integer,
    dolphin_count integer,
    fish_count integer,
    shrimp_count integer
);


--
-- Name: moralis_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_stats_id_seq OWNED BY public.moralis_stats.id;


--
-- Name: moralis_swaps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_swaps (
    id integer NOT NULL,
    transaction_hash character varying(66),
    block_number bigint,
    block_timestamp timestamp without time zone,
    transaction_type character varying(10),
    wallet_address character varying(42),
    bought_token character varying(42),
    bought_amount numeric(40,18),
    bought_usd numeric(30,2),
    sold_token character varying(42),
    sold_amount numeric(40,18),
    sold_usd numeric(30,2),
    total_usd numeric(30,2),
    exchange_name character varying(100),
    pair_address character varying(42),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_swaps_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_swaps_correct (
    transaction_hash text NOT NULL,
    transaction_index integer,
    transaction_type text,
    block_timestamp timestamp without time zone,
    block_number bigint,
    sub_category text,
    wallet_address text,
    wallet_address_label text,
    entity text,
    entity_logo text,
    pair_address text,
    pair_label text,
    exchange_address text,
    exchange_name text,
    exchange_logo text,
    bought_address text,
    bought_name text,
    bought_symbol text,
    bought_logo text,
    bought_amount numeric(40,18),
    bought_usd_price numeric(40,18),
    bought_usd_amount numeric(40,18),
    sold_address text,
    sold_name text,
    sold_symbol text,
    sold_logo text,
    sold_amount numeric(40,18),
    sold_usd_price numeric(40,18),
    sold_usd_amount numeric(40,18),
    base_quote_price text,
    total_value_usd numeric(40,18),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_swaps_enhanced; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_swaps_enhanced (
    id integer NOT NULL,
    transaction_hash text,
    transaction_index integer,
    transaction_type text,
    sub_category text,
    block_number bigint,
    block_timestamp timestamp without time zone,
    wallet_address text,
    wallet_address_label text,
    entity text,
    entity_logo text,
    pair_address text,
    pair_label text,
    exchange_address text,
    exchange_name text,
    exchange_logo text,
    bought_address text,
    bought_name text,
    bought_symbol text,
    bought_logo text,
    bought_amount numeric(40,18),
    bought_usd_price numeric(20,8),
    bought_usd_amount numeric(20,2),
    sold_address text,
    sold_name text,
    sold_symbol text,
    sold_logo text,
    sold_amount numeric(40,18),
    sold_usd_price numeric(20,8),
    sold_usd_amount numeric(20,2),
    base_quote_price numeric(40,18),
    total_value_usd numeric(20,2),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_swaps_enhanced_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_swaps_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_swaps_enhanced_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_swaps_enhanced_id_seq OWNED BY public.moralis_swaps_enhanced.id;


--
-- Name: moralis_swaps_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_swaps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_swaps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_swaps_id_seq OWNED BY public.moralis_swaps.id;


--
-- Name: moralis_token_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_analytics (
    id integer NOT NULL,
    token_address character varying(42),
    buy_volume_5m numeric(30,2),
    sell_volume_5m numeric(30,2),
    buy_volume_1h numeric(30,2),
    sell_volume_1h numeric(30,2),
    buy_volume_24h numeric(30,2),
    sell_volume_24h numeric(30,2),
    buyers_5m integer,
    sellers_5m integer,
    buyers_24h integer,
    sellers_24h integer,
    buys_24h integer,
    sells_24h integer,
    liquidity_usd numeric(30,2),
    fdv numeric(30,2),
    usd_price numeric(30,10),
    price_change_24h numeric(10,4),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_analytics_correct; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_analytics_correct (
    id integer NOT NULL,
    token_address text,
    category_id text,
    total_buy_volume_5m numeric(40,18),
    total_buy_volume_1h numeric(40,18),
    total_buy_volume_6h numeric(40,18),
    total_buy_volume_24h numeric(40,18),
    total_sell_volume_5m numeric(40,18),
    total_sell_volume_1h numeric(40,18),
    total_sell_volume_6h numeric(40,18),
    total_sell_volume_24h numeric(40,18),
    total_buyers_5m integer,
    total_buyers_1h integer,
    total_buyers_6h integer,
    total_buyers_24h integer,
    total_sellers_5m integer,
    total_sellers_1h integer,
    total_sellers_6h integer,
    total_sellers_24h integer,
    total_buys_5m integer,
    total_buys_1h integer,
    total_buys_6h integer,
    total_buys_24h integer,
    total_sells_5m integer,
    total_sells_1h integer,
    total_sells_6h integer,
    total_sells_24h integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_analytics_correct_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_analytics_correct_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_analytics_correct_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_analytics_correct_id_seq OWNED BY public.moralis_token_analytics_correct.id;


--
-- Name: moralis_token_analytics_enhanced; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_analytics_enhanced (
    id integer NOT NULL,
    token_address text,
    category_id text,
    buy_volume_5m numeric(20,2),
    buy_volume_1h numeric(20,2),
    buy_volume_6h numeric(20,2),
    buy_volume_24h numeric(20,2),
    sell_volume_5m numeric(20,2),
    sell_volume_1h numeric(20,2),
    sell_volume_6h numeric(20,2),
    sell_volume_24h numeric(20,2),
    buyers_5m integer,
    buyers_1h integer,
    buyers_6h integer,
    buyers_24h integer,
    sellers_5m integer,
    sellers_1h integer,
    sellers_6h integer,
    sellers_24h integer,
    buys_5m integer,
    buys_1h integer,
    buys_6h integer,
    buys_24h integer,
    sells_5m integer,
    sells_1h integer,
    sells_6h integer,
    sells_24h integer,
    liquidity_5m numeric(20,2),
    liquidity_1h numeric(20,2),
    liquidity_6h numeric(20,2),
    liquidity_24h numeric(20,2),
    fdv_5m numeric(20,2),
    fdv_1h numeric(20,2),
    fdv_6h numeric(20,2),
    fdv_24h numeric(20,2),
    price_change_5m numeric(10,6),
    price_change_1h numeric(10,6),
    price_change_6h numeric(10,6),
    price_change_24h numeric(10,6),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_analytics_enhanced_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_analytics_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_analytics_enhanced_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_analytics_enhanced_id_seq OWNED BY public.moralis_token_analytics_enhanced.id;


--
-- Name: moralis_token_analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_analytics_id_seq OWNED BY public.moralis_token_analytics.id;


--
-- Name: moralis_token_holder_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_holder_stats (
    id integer NOT NULL,
    token_address text,
    total_holders integer,
    holder_supply_top10 numeric(40,18),
    holder_supply_top10_percent numeric(10,6),
    holder_supply_top25 numeric(40,18),
    holder_supply_top25_percent numeric(10,6),
    holder_supply_top50 numeric(40,18),
    holder_supply_top50_percent numeric(10,6),
    holder_supply_top100 numeric(40,18),
    holder_supply_top100_percent numeric(10,6),
    holder_change_5min integer,
    holder_change_5min_percent numeric(10,6),
    holder_change_1h integer,
    holder_change_1h_percent numeric(10,6),
    holder_change_24h integer,
    holder_change_24h_percent numeric(10,6),
    holders_by_swap integer,
    holders_by_transfer integer,
    holders_by_airdrop integer,
    whales_count integer,
    sharks_count integer,
    dolphins_count integer,
    fish_count integer,
    octopus_count integer,
    crabs_count integer,
    shrimps_count integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_holder_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_holder_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_holder_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_holder_stats_id_seq OWNED BY public.moralis_token_holder_stats.id;


--
-- Name: moralis_token_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_stats (
    id integer NOT NULL,
    token_address character varying(42),
    token_name character varying(100),
    token_symbol character varying(20),
    total_supply numeric(40,18),
    circulating_supply numeric(40,18),
    market_cap numeric(30,2),
    fdv numeric(30,2),
    transfers_total bigint,
    holders_count integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_stats_id_seq OWNED BY public.moralis_token_stats.id;


--
-- Name: moralis_token_stats_simple; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_stats_simple (
    id integer NOT NULL,
    token_address text,
    total_transfers bigint,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_stats_simple_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_stats_simple_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_stats_simple_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_stats_simple_id_seq OWNED BY public.moralis_token_stats_simple.id;


--
-- Name: moralis_token_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_token_transfers (
    id integer NOT NULL,
    transaction_hash character varying(66),
    block_number bigint,
    block_timestamp timestamp without time zone,
    from_address character varying(42),
    to_address character varying(42),
    value numeric(40,18),
    value_usd numeric(30,2),
    token_address character varying(42),
    token_symbol character varying(20),
    transaction_index integer,
    log_index integer,
    is_spam boolean DEFAULT false,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_token_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_token_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_token_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_token_transfers_id_seq OWNED BY public.moralis_token_transfers.id;


--
-- Name: moralis_top_gainers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_top_gainers (
    id integer NOT NULL,
    token_address text,
    wallet_address text,
    avg_buy_price_usd numeric(20,8),
    avg_cost_of_quantity_sold numeric(20,8),
    avg_sell_price_usd numeric(20,8),
    count_of_trades integer,
    realized_profit_percentage numeric(10,6),
    realized_profit_usd numeric(20,2),
    total_sold_usd numeric(20,2),
    total_tokens_bought numeric(40,18),
    total_tokens_sold numeric(40,18),
    total_usd_invested numeric(20,2),
    timeframe text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_top_gainers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_top_gainers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_top_gainers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_top_gainers_id_seq OWNED BY public.moralis_top_gainers.id;


--
-- Name: moralis_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moralis_transfers (
    id integer NOT NULL,
    transaction_hash text,
    block_number bigint,
    block_timestamp timestamp without time zone,
    from_address text,
    to_address text,
    value numeric(40,18),
    value_decimal numeric(20,8),
    token_address text,
    token_name text,
    token_symbol text,
    token_decimals integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: moralis_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moralis_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moralis_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moralis_transfers_id_seq OWNED BY public.moralis_transfers.id;


--
-- Name: token_distribution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_distribution (
    id integer NOT NULL,
    top_10_concentration numeric(10,4),
    top_50_concentration numeric(10,4),
    top_100_concentration numeric(10,4),
    gini_coefficient numeric(10,4),
    unique_holders integer,
    new_holders_24h integer,
    whale_count integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: token_distribution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_distribution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_distribution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_distribution_id_seq OWNED BY public.token_distribution.id;


--
-- Name: token_prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_prices (
    id integer NOT NULL,
    chain_id integer NOT NULL,
    token_symbol character varying(20) NOT NULL,
    token_address character varying(42),
    price_usd numeric(20,8),
    volume_24h numeric(30,2),
    price_change_24h numeric(10,4),
    market_cap numeric(30,2),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: token_prices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_prices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_prices_id_seq OWNED BY public.token_prices.id;


--
-- Name: top_pairs_24h; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.top_pairs_24h AS
 SELECT dex_trades.pair,
    dex_trades.chain_name,
    dex_trades.dex_name,
    count(*) AS trade_count,
    sum(dex_trades.value_usd) AS volume_usd,
    avg(dex_trades.price) AS avg_price,
    max(dex_trades."timestamp") AS last_trade
   FROM public.dex_trades
  WHERE (dex_trades."timestamp" > (now() - '24:00:00'::interval))
  GROUP BY dex_trades.pair, dex_trades.chain_name, dex_trades.dex_name
  ORDER BY (sum(dex_trades.value_usd)) DESC
 LIMIT 100
  WITH NO DATA;


--
-- Name: wallet_activity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wallet_activity (
    id integer NOT NULL,
    chain_id integer NOT NULL,
    wallet_address character varying(42) NOT NULL,
    wallet_label character varying(100),
    total_trades integer DEFAULT 0,
    volume_24h numeric(30,2),
    profit_loss numeric(20,2),
    win_rate numeric(5,2),
    tokens_traded integer,
    last_trade_time timestamp without time zone,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wallet_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wallet_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wallet_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wallet_activity_id_seq OWNED BY public.wallet_activity.id;


--
-- Name: wallet_pnl; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wallet_pnl (
    id integer NOT NULL,
    wallet_address character varying(42),
    token_address character varying(42),
    total_bought numeric(40,18),
    total_sold numeric(40,18),
    avg_buy_price numeric(30,10),
    avg_sell_price numeric(30,10),
    realized_pnl numeric(30,2),
    unrealized_pnl numeric(30,2),
    trade_count integer,
    first_trade timestamp without time zone,
    last_trade timestamp without time zone,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wallet_pnl_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wallet_pnl_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wallet_pnl_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wallet_pnl_id_seq OWNED BY public.wallet_pnl.id;


--
-- Name: wash_trade_suspects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wash_trade_suspects (
    id integer NOT NULL,
    wallet_address character varying(42),
    related_wallets text[],
    suspicious_tx_count integer,
    circular_volume numeric(30,2),
    detection_score numeric(5,2),
    evidence jsonb,
    detected_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wash_trade_suspects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wash_trade_suspects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wash_trade_suspects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wash_trade_suspects_id_seq OWNED BY public.wash_trade_suspects.id;


--
-- Name: wash_trading_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wash_trading_alerts (
    id integer NOT NULL,
    wallet_address character varying(42),
    pair_address character varying(42),
    detection_type character varying(50),
    buy_count integer,
    sell_count integer,
    total_volume numeric(30,2),
    time_window_minutes integer,
    confidence_score numeric(5,2),
    details jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wash_trading_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wash_trading_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wash_trading_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wash_trading_alerts_id_seq OWNED BY public.wash_trading_alerts.id;


--
-- Name: wash_trading_complete; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wash_trading_complete (
    id integer NOT NULL,
    wallet_address character varying(42),
    pair_address character varying(42),
    detection_type character varying(50),
    buy_count integer,
    sell_count integer,
    round_trips integer,
    avg_hold_time_seconds integer,
    total_volume numeric(30,2),
    net_pnl numeric(30,2),
    time_window_minutes integer,
    confidence_score numeric(5,2),
    related_wallets text[],
    details jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wash_trading_complete_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wash_trading_complete_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wash_trading_complete_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wash_trading_complete_id_seq OWNED BY public.wash_trading_complete.id;


--
-- Name: bsc_liquidity_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_liquidity_events ALTER COLUMN id SET DEFAULT nextval('public.bsc_liquidity_events_id_seq'::regclass);


--
-- Name: bsc_pool_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_pool_metrics ALTER COLUMN id SET DEFAULT nextval('public.bsc_pool_metrics_id_seq'::regclass);


--
-- Name: bsc_trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_trades ALTER COLUMN id SET DEFAULT nextval('public.bsc_trades_id_seq'::regclass);


--
-- Name: bsc_wallet_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_wallet_metrics ALTER COLUMN id SET DEFAULT nextval('public.bsc_wallet_metrics_id_seq'::regclass);


--
-- Name: chain_stats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_stats ALTER COLUMN id SET DEFAULT nextval('public.chain_stats_id_seq'::regclass);


--
-- Name: dex_trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dex_trades ALTER COLUMN id SET DEFAULT nextval('public.dex_trades_id_seq'::regclass);


--
-- Name: liquidity_pools id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_pools ALTER COLUMN id SET DEFAULT nextval('public.liquidity_pools_id_seq'::regclass);


--
-- Name: manipulation_alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulation_alerts ALTER COLUMN id SET DEFAULT nextval('public.manipulation_alerts_id_seq'::regclass);


--
-- Name: market_manipulation_alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.market_manipulation_alerts ALTER COLUMN id SET DEFAULT nextval('public.market_manipulation_alerts_id_seq'::regclass);


--
-- Name: moralis_historical_holders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders ALTER COLUMN id SET DEFAULT nextval('public.moralis_historical_holders_id_seq'::regclass);


--
-- Name: moralis_historical_holders_correct id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_correct ALTER COLUMN id SET DEFAULT nextval('public.moralis_historical_holders_correct_id_seq'::regclass);


--
-- Name: moralis_historical_holders_enhanced id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_enhanced ALTER COLUMN id SET DEFAULT nextval('public.moralis_historical_holders_enhanced_id_seq'::regclass);


--
-- Name: moralis_holder_distribution id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_distribution ALTER COLUMN id SET DEFAULT nextval('public.moralis_holder_distribution_id_seq'::regclass);


--
-- Name: moralis_holder_stats_complete id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_stats_complete ALTER COLUMN id SET DEFAULT nextval('public.moralis_holder_stats_complete_id_seq'::regclass);


--
-- Name: moralis_holder_stats_correct id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_stats_correct ALTER COLUMN id SET DEFAULT nextval('public.moralis_holder_stats_correct_id_seq'::regclass);


--
-- Name: moralis_holders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holders ALTER COLUMN id SET DEFAULT nextval('public.moralis_holders_id_seq'::regclass);


--
-- Name: moralis_liquidity_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_liquidity_changes ALTER COLUMN id SET DEFAULT nextval('public.moralis_liquidity_changes_id_seq'::regclass);


--
-- Name: moralis_metrics_summary id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_metrics_summary ALTER COLUMN id SET DEFAULT nextval('public.moralis_metrics_summary_id_seq'::regclass);


--
-- Name: moralis_pair_stats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats ALTER COLUMN id SET DEFAULT nextval('public.moralis_pair_stats_id_seq'::regclass);


--
-- Name: moralis_pair_stats_correct id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_correct ALTER COLUMN id SET DEFAULT nextval('public.moralis_pair_stats_correct_id_seq'::regclass);


--
-- Name: moralis_pair_stats_enhanced id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_enhanced ALTER COLUMN id SET DEFAULT nextval('public.moralis_pair_stats_enhanced_id_seq'::regclass);


--
-- Name: moralis_snipers_complete id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_complete ALTER COLUMN id SET DEFAULT nextval('public.moralis_snipers_complete_id_seq'::regclass);


--
-- Name: moralis_snipers_correct id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_correct ALTER COLUMN id SET DEFAULT nextval('public.moralis_snipers_correct_id_seq'::regclass);


--
-- Name: moralis_snipers_enhanced id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_enhanced ALTER COLUMN id SET DEFAULT nextval('public.moralis_snipers_enhanced_id_seq'::regclass);


--
-- Name: moralis_stats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_stats ALTER COLUMN id SET DEFAULT nextval('public.moralis_stats_id_seq'::regclass);


--
-- Name: moralis_swaps id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps ALTER COLUMN id SET DEFAULT nextval('public.moralis_swaps_id_seq'::regclass);


--
-- Name: moralis_swaps_enhanced id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps_enhanced ALTER COLUMN id SET DEFAULT nextval('public.moralis_swaps_enhanced_id_seq'::regclass);


--
-- Name: moralis_token_analytics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_analytics_id_seq'::regclass);


--
-- Name: moralis_token_analytics_correct id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_correct ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_analytics_correct_id_seq'::regclass);


--
-- Name: moralis_token_analytics_enhanced id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_enhanced ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_analytics_enhanced_id_seq'::regclass);


--
-- Name: moralis_token_holder_stats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_holder_stats ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_holder_stats_id_seq'::regclass);


--
-- Name: moralis_token_stats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_stats ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_stats_id_seq'::regclass);


--
-- Name: moralis_token_stats_simple id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_stats_simple ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_stats_simple_id_seq'::regclass);


--
-- Name: moralis_token_transfers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_transfers ALTER COLUMN id SET DEFAULT nextval('public.moralis_token_transfers_id_seq'::regclass);


--
-- Name: moralis_top_gainers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_top_gainers ALTER COLUMN id SET DEFAULT nextval('public.moralis_top_gainers_id_seq'::regclass);


--
-- Name: moralis_transfers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_transfers ALTER COLUMN id SET DEFAULT nextval('public.moralis_transfers_id_seq'::regclass);


--
-- Name: token_distribution id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_distribution ALTER COLUMN id SET DEFAULT nextval('public.token_distribution_id_seq'::regclass);


--
-- Name: token_prices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_prices ALTER COLUMN id SET DEFAULT nextval('public.token_prices_id_seq'::regclass);


--
-- Name: wallet_activity id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wallet_activity ALTER COLUMN id SET DEFAULT nextval('public.wallet_activity_id_seq'::regclass);


--
-- Name: wallet_pnl id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wallet_pnl ALTER COLUMN id SET DEFAULT nextval('public.wallet_pnl_id_seq'::regclass);


--
-- Name: wash_trade_suspects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trade_suspects ALTER COLUMN id SET DEFAULT nextval('public.wash_trade_suspects_id_seq'::regclass);


--
-- Name: wash_trading_alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trading_alerts ALTER COLUMN id SET DEFAULT nextval('public.wash_trading_alerts_id_seq'::regclass);


--
-- Name: wash_trading_complete id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trading_complete ALTER COLUMN id SET DEFAULT nextval('public.wash_trading_complete_id_seq'::regclass);


--
-- Name: bsc_liquidity_events bsc_liquidity_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_liquidity_events
    ADD CONSTRAINT bsc_liquidity_events_pkey PRIMARY KEY (id);


--
-- Name: bsc_liquidity_events bsc_liquidity_events_tx_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_liquidity_events
    ADD CONSTRAINT bsc_liquidity_events_tx_hash_key UNIQUE (tx_hash);


--
-- Name: bsc_pool_metrics bsc_pool_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_pool_metrics
    ADD CONSTRAINT bsc_pool_metrics_pkey PRIMARY KEY (id);


--
-- Name: bsc_trades bsc_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_trades
    ADD CONSTRAINT bsc_trades_pkey PRIMARY KEY (id);


--
-- Name: bsc_trades bsc_trades_tx_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_trades
    ADD CONSTRAINT bsc_trades_tx_hash_key UNIQUE (tx_hash);


--
-- Name: bsc_wallet_metrics bsc_wallet_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bsc_wallet_metrics
    ADD CONSTRAINT bsc_wallet_metrics_pkey PRIMARY KEY (id);


--
-- Name: chain_stats chain_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chain_stats
    ADD CONSTRAINT chain_stats_pkey PRIMARY KEY (id);


--
-- Name: dex_trades dex_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dex_trades
    ADD CONSTRAINT dex_trades_pkey PRIMARY KEY (id);


--
-- Name: liquidity_pools liquidity_pools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_pools
    ADD CONSTRAINT liquidity_pools_pkey PRIMARY KEY (id);


--
-- Name: manipulation_alerts manipulation_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulation_alerts
    ADD CONSTRAINT manipulation_alerts_pkey PRIMARY KEY (id);


--
-- Name: market_manipulation_alerts market_manipulation_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.market_manipulation_alerts
    ADD CONSTRAINT market_manipulation_alerts_pkey PRIMARY KEY (id);


--
-- Name: moralis_historical_holders_correct moralis_historical_holders_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_correct
    ADD CONSTRAINT moralis_historical_holders_correct_pkey PRIMARY KEY (id);


--
-- Name: moralis_historical_holders_correct moralis_historical_holders_correct_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_correct
    ADD CONSTRAINT moralis_historical_holders_correct_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_historical_holders_enhanced moralis_historical_holders_enhanced_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_enhanced
    ADD CONSTRAINT moralis_historical_holders_enhanced_pkey PRIMARY KEY (id);


--
-- Name: moralis_historical_holders_enhanced moralis_historical_holders_enhanced_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders_enhanced
    ADD CONSTRAINT moralis_historical_holders_enhanced_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_historical_holders moralis_historical_holders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_historical_holders
    ADD CONSTRAINT moralis_historical_holders_pkey PRIMARY KEY (id);


--
-- Name: moralis_holder_distribution moralis_holder_distribution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_distribution
    ADD CONSTRAINT moralis_holder_distribution_pkey PRIMARY KEY (id);


--
-- Name: moralis_holder_distribution moralis_holder_distribution_token_address_holder_address_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_distribution
    ADD CONSTRAINT moralis_holder_distribution_token_address_holder_address_key UNIQUE (token_address, holder_address);


--
-- Name: moralis_holder_stats_complete moralis_holder_stats_complete_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_stats_complete
    ADD CONSTRAINT moralis_holder_stats_complete_pkey PRIMARY KEY (id);


--
-- Name: moralis_holder_stats_correct moralis_holder_stats_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_stats_correct
    ADD CONSTRAINT moralis_holder_stats_correct_pkey PRIMARY KEY (id);


--
-- Name: moralis_holder_stats_correct moralis_holder_stats_correct_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holder_stats_correct
    ADD CONSTRAINT moralis_holder_stats_correct_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_holders moralis_holders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holders
    ADD CONSTRAINT moralis_holders_pkey PRIMARY KEY (id);


--
-- Name: moralis_holders moralis_holders_token_address_holder_address_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_holders
    ADD CONSTRAINT moralis_holders_token_address_holder_address_key UNIQUE (token_address, holder_address);


--
-- Name: moralis_liquidity_changes moralis_liquidity_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_liquidity_changes
    ADD CONSTRAINT moralis_liquidity_changes_pkey PRIMARY KEY (id);


--
-- Name: moralis_metrics_summary moralis_metrics_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_metrics_summary
    ADD CONSTRAINT moralis_metrics_summary_pkey PRIMARY KEY (id);


--
-- Name: moralis_pair_stats_correct moralis_pair_stats_correct_pair_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_correct
    ADD CONSTRAINT moralis_pair_stats_correct_pair_address_timestamp_key UNIQUE (pair_address, "timestamp");


--
-- Name: moralis_pair_stats_correct moralis_pair_stats_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_correct
    ADD CONSTRAINT moralis_pair_stats_correct_pkey PRIMARY KEY (id);


--
-- Name: moralis_pair_stats_enhanced moralis_pair_stats_enhanced_pair_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_enhanced
    ADD CONSTRAINT moralis_pair_stats_enhanced_pair_address_timestamp_key UNIQUE (pair_address, "timestamp");


--
-- Name: moralis_pair_stats_enhanced moralis_pair_stats_enhanced_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats_enhanced
    ADD CONSTRAINT moralis_pair_stats_enhanced_pkey PRIMARY KEY (id);


--
-- Name: moralis_pair_stats moralis_pair_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_pair_stats
    ADD CONSTRAINT moralis_pair_stats_pkey PRIMARY KEY (id);


--
-- Name: moralis_snipers_complete moralis_snipers_complete_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_complete
    ADD CONSTRAINT moralis_snipers_complete_pkey PRIMARY KEY (id);


--
-- Name: moralis_snipers_correct moralis_snipers_correct_pair_address_wallet_address_timesta_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_correct
    ADD CONSTRAINT moralis_snipers_correct_pair_address_wallet_address_timesta_key UNIQUE (pair_address, wallet_address, "timestamp");


--
-- Name: moralis_snipers_correct moralis_snipers_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_correct
    ADD CONSTRAINT moralis_snipers_correct_pkey PRIMARY KEY (id);


--
-- Name: moralis_snipers_enhanced moralis_snipers_enhanced_pair_address_wallet_address_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_enhanced
    ADD CONSTRAINT moralis_snipers_enhanced_pair_address_wallet_address_key UNIQUE (pair_address, wallet_address);


--
-- Name: moralis_snipers_enhanced moralis_snipers_enhanced_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_snipers_enhanced
    ADD CONSTRAINT moralis_snipers_enhanced_pkey PRIMARY KEY (id);


--
-- Name: moralis_stats moralis_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_stats
    ADD CONSTRAINT moralis_stats_pkey PRIMARY KEY (id);


--
-- Name: moralis_swaps_correct moralis_swaps_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps_correct
    ADD CONSTRAINT moralis_swaps_correct_pkey PRIMARY KEY (transaction_hash);


--
-- Name: moralis_swaps_enhanced moralis_swaps_enhanced_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps_enhanced
    ADD CONSTRAINT moralis_swaps_enhanced_pkey PRIMARY KEY (id);


--
-- Name: moralis_swaps_enhanced moralis_swaps_enhanced_transaction_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps_enhanced
    ADD CONSTRAINT moralis_swaps_enhanced_transaction_hash_key UNIQUE (transaction_hash);


--
-- Name: moralis_swaps moralis_swaps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps
    ADD CONSTRAINT moralis_swaps_pkey PRIMARY KEY (id);


--
-- Name: moralis_swaps moralis_swaps_transaction_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_swaps
    ADD CONSTRAINT moralis_swaps_transaction_hash_key UNIQUE (transaction_hash);


--
-- Name: moralis_token_analytics_correct moralis_token_analytics_correct_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_correct
    ADD CONSTRAINT moralis_token_analytics_correct_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_analytics_correct moralis_token_analytics_correct_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_correct
    ADD CONSTRAINT moralis_token_analytics_correct_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_token_analytics_enhanced moralis_token_analytics_enhanced_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_enhanced
    ADD CONSTRAINT moralis_token_analytics_enhanced_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_analytics_enhanced moralis_token_analytics_enhanced_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics_enhanced
    ADD CONSTRAINT moralis_token_analytics_enhanced_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_token_analytics moralis_token_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_analytics
    ADD CONSTRAINT moralis_token_analytics_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_holder_stats moralis_token_holder_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_holder_stats
    ADD CONSTRAINT moralis_token_holder_stats_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_holder_stats moralis_token_holder_stats_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_holder_stats
    ADD CONSTRAINT moralis_token_holder_stats_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_token_stats moralis_token_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_stats
    ADD CONSTRAINT moralis_token_stats_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_stats_simple moralis_token_stats_simple_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_stats_simple
    ADD CONSTRAINT moralis_token_stats_simple_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_stats_simple moralis_token_stats_simple_token_address_timestamp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_stats_simple
    ADD CONSTRAINT moralis_token_stats_simple_token_address_timestamp_key UNIQUE (token_address, "timestamp");


--
-- Name: moralis_token_transfers moralis_token_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_transfers
    ADD CONSTRAINT moralis_token_transfers_pkey PRIMARY KEY (id);


--
-- Name: moralis_token_transfers moralis_token_transfers_transaction_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_token_transfers
    ADD CONSTRAINT moralis_token_transfers_transaction_hash_key UNIQUE (transaction_hash);


--
-- Name: moralis_top_gainers moralis_top_gainers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_top_gainers
    ADD CONSTRAINT moralis_top_gainers_pkey PRIMARY KEY (id);


--
-- Name: moralis_top_gainers moralis_top_gainers_token_address_wallet_address_timeframe_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_top_gainers
    ADD CONSTRAINT moralis_top_gainers_token_address_wallet_address_timeframe_key UNIQUE (token_address, wallet_address, timeframe);


--
-- Name: moralis_transfers moralis_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_transfers
    ADD CONSTRAINT moralis_transfers_pkey PRIMARY KEY (id);


--
-- Name: moralis_transfers moralis_transfers_transaction_hash_from_address_to_address__key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moralis_transfers
    ADD CONSTRAINT moralis_transfers_transaction_hash_from_address_to_address__key UNIQUE (transaction_hash, from_address, to_address, value);


--
-- Name: token_distribution token_distribution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_distribution
    ADD CONSTRAINT token_distribution_pkey PRIMARY KEY (id);


--
-- Name: token_prices token_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_prices
    ADD CONSTRAINT token_prices_pkey PRIMARY KEY (id);


--
-- Name: wallet_activity wallet_activity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wallet_activity
    ADD CONSTRAINT wallet_activity_pkey PRIMARY KEY (id);


--
-- Name: wallet_pnl wallet_pnl_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wallet_pnl
    ADD CONSTRAINT wallet_pnl_pkey PRIMARY KEY (id);


--
-- Name: wallet_pnl wallet_pnl_wallet_address_token_address_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wallet_pnl
    ADD CONSTRAINT wallet_pnl_wallet_address_token_address_key UNIQUE (wallet_address, token_address);


--
-- Name: wash_trade_suspects wash_trade_suspects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trade_suspects
    ADD CONSTRAINT wash_trade_suspects_pkey PRIMARY KEY (id);


--
-- Name: wash_trading_alerts wash_trading_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trading_alerts
    ADD CONSTRAINT wash_trading_alerts_pkey PRIMARY KEY (id);


--
-- Name: wash_trading_complete wash_trading_complete_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wash_trading_complete
    ADD CONSTRAINT wash_trading_complete_pkey PRIMARY KEY (id);


--
-- Name: hourly_dex_stats_hour_chain_name_dex_name_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX hourly_dex_stats_hour_chain_name_dex_name_idx ON public.hourly_dex_stats USING btree (hour, chain_name, dex_name);


--
-- Name: idx_analytics_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_timestamp ON public.moralis_token_analytics_correct USING btree ("timestamp");


--
-- Name: idx_analytics_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_token ON public.moralis_token_analytics_correct USING btree (token_address);


--
-- Name: idx_bsc_trades_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bsc_trades_timestamp ON public.bsc_trades USING btree ("timestamp" DESC);


--
-- Name: idx_bsc_trades_trader; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bsc_trades_trader ON public.bsc_trades USING btree (trader_address);


--
-- Name: idx_bsc_wallet_pnl; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bsc_wallet_pnl ON public.bsc_wallet_metrics USING btree (realized_pnl DESC);


--
-- Name: idx_bsc_wallet_volume; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bsc_wallet_volume ON public.bsc_wallet_metrics USING btree (total_volume_usd DESC);


--
-- Name: idx_dex_trades_chain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dex_trades_chain ON public.dex_trades USING btree (chain_id, "timestamp" DESC);


--
-- Name: idx_dex_trades_dex; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dex_trades_dex ON public.dex_trades USING btree (dex_name, "timestamp" DESC);


--
-- Name: idx_dex_trades_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dex_trades_pair ON public.dex_trades USING btree (pair);


--
-- Name: idx_dex_trades_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dex_trades_timestamp ON public.dex_trades USING btree ("timestamp" DESC);


--
-- Name: idx_dex_trades_trader; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dex_trades_trader ON public.dex_trades USING btree (trader_address);


--
-- Name: idx_historical_holders_data; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historical_holders_data ON public.moralis_historical_holders USING btree (data_timestamp DESC);


--
-- Name: idx_historical_holders_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historical_holders_timestamp ON public.moralis_historical_holders_correct USING btree ("timestamp");


--
-- Name: idx_historical_holders_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historical_holders_token ON public.moralis_historical_holders_enhanced USING btree (token_address, "timestamp");


--
-- Name: idx_holder_distribution_balance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_holder_distribution_balance ON public.moralis_holder_distribution USING btree (balance_usd DESC);


--
-- Name: idx_holder_stats_complete_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_holder_stats_complete_timestamp ON public.moralis_holder_stats_complete USING btree ("timestamp" DESC);


--
-- Name: idx_holder_stats_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_holder_stats_timestamp ON public.moralis_holder_stats_correct USING btree ("timestamp");


--
-- Name: idx_holder_stats_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_holder_stats_token ON public.moralis_token_holder_stats USING btree (token_address);


--
-- Name: idx_liquidity_changes_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_liquidity_changes_time ON public.moralis_liquidity_changes USING btree (block_timestamp DESC);


--
-- Name: idx_liquidity_pools_dex; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_liquidity_pools_dex ON public.liquidity_pools USING btree (dex_name, "timestamp" DESC);


--
-- Name: idx_liquidity_pools_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_liquidity_pools_timestamp ON public.liquidity_pools USING btree ("timestamp" DESC);


--
-- Name: idx_manipulation_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manipulation_timestamp ON public.market_manipulation_alerts USING btree ("timestamp" DESC);


--
-- Name: idx_pair_stats_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pair_stats_pair ON public.moralis_pair_stats_enhanced USING btree (pair_address);


--
-- Name: idx_pair_stats_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pair_stats_timestamp ON public.moralis_pair_stats_correct USING btree ("timestamp");


--
-- Name: idx_pnl_profit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pnl_profit ON public.wallet_pnl USING btree (realized_pnl DESC);


--
-- Name: idx_pool_metrics_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pool_metrics_timestamp ON public.bsc_pool_metrics USING btree ("timestamp" DESC);


--
-- Name: idx_snipers_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snipers_pair ON public.moralis_snipers_enhanced USING btree (pair_address);


--
-- Name: idx_snipers_profit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snipers_profit ON public.moralis_snipers_complete USING btree (realized_profit_pct DESC);


--
-- Name: idx_snipers_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snipers_timestamp ON public.moralis_snipers_correct USING btree ("timestamp");


--
-- Name: idx_snipers_wallet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snipers_wallet ON public.moralis_snipers_complete USING btree (wallet_address);


--
-- Name: idx_swaps_enhanced_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_enhanced_timestamp ON public.moralis_swaps_enhanced USING btree (block_timestamp);


--
-- Name: idx_swaps_enhanced_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_enhanced_type ON public.moralis_swaps_enhanced USING btree (transaction_type);


--
-- Name: idx_swaps_enhanced_wallet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_enhanced_wallet ON public.moralis_swaps_enhanced USING btree (wallet_address);


--
-- Name: idx_swaps_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_timestamp ON public.moralis_swaps USING btree (block_timestamp DESC);


--
-- Name: idx_swaps_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_type ON public.moralis_swaps_correct USING btree (transaction_type);


--
-- Name: idx_swaps_wallet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swaps_wallet ON public.moralis_swaps USING btree (wallet_address);


--
-- Name: idx_token_analytics_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_analytics_token ON public.moralis_token_analytics_enhanced USING btree (token_address);


--
-- Name: idx_token_prices_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_prices_symbol ON public.token_prices USING btree (token_symbol, "timestamp" DESC);


--
-- Name: idx_token_prices_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_prices_timestamp ON public.token_prices USING btree ("timestamp" DESC);


--
-- Name: idx_token_stats_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_stats_timestamp ON public.moralis_token_stats USING btree ("timestamp" DESC);


--
-- Name: idx_top_gainers_profit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_top_gainers_profit ON public.moralis_top_gainers USING btree (realized_profit_usd DESC);


--
-- Name: idx_top_gainers_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_top_gainers_token ON public.moralis_top_gainers USING btree (token_address);


--
-- Name: idx_transfers_addresses; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transfers_addresses ON public.moralis_token_transfers USING btree (from_address, to_address);


--
-- Name: idx_transfers_block; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transfers_block ON public.moralis_token_transfers USING btree (block_timestamp DESC);


--
-- Name: idx_wallet_activity_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wallet_activity_timestamp ON public.wallet_activity USING btree ("timestamp" DESC);


--
-- Name: idx_wallet_activity_volume; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wallet_activity_volume ON public.wallet_activity USING btree (volume_24h DESC);


--
-- Name: idx_wash_trading_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wash_trading_confidence ON public.wash_trading_complete USING btree (confidence_score DESC);


--
-- Name: idx_wash_trading_wallet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wash_trading_wallet ON public.wash_trading_alerts USING btree (wallet_address);


--
-- Name: top_pairs_24h_pair_chain_name_dex_name_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX top_pairs_24h_pair_chain_name_dex_name_idx ON public.top_pairs_24h USING btree (pair, chain_name, dex_name);


--
-- PostgreSQL database dump complete
--

\unrestrict 0CaR58IbJqlwtDSaMgoDPjh1JdFLfV3WOH9Rq51LzRhHRlrc2kbl8m6zcXF8J9N

