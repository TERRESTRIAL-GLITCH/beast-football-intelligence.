import streamlit as st
import pandas as pd
import numpy as np
import feedparser
from email.utils import parsedate_to_datetime
from datetime import timezone

st.set_page_config(page_title="BEAST Football Intelligence", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1.4rem;max-width:1450px}
.hero{padding:1.35rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#111827,#14532d);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2.25rem}.hero p{margin:.45rem 0 0;color:#d1fae5}
.news{padding:.8rem 1rem;border:1px solid rgba(128,128,128,.3);border-radius:12px;margin:.5rem 0}
</style>
<div class="hero"><h1>⚽ BEAST</h1><p>Football intelligence · BTTS predictions · Match news</p></div>
""", unsafe_allow_html=True)

FEEDS = [
 ("BBC Sport Football","https://feeds.bbci.co.uk/sport/football/rss.xml"),
 ("Sky Sports Football","https://www.skysports.com/rss/12040"),
 ("ESPN Soccer","https://www.espn.com/espn/rss/soccer/news"),
 ("Google News Football","https://news.google.com/rss/search?q=football+injury+team+news&hl=en-GB&gl=GB&ceid=GB:en"),
]

@st.cache_data(ttl=900, show_spinner=False)
def get_news():
    rows, seen = [], set()
    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:20]:
                link, title = e.get("link", ""), e.get("title", "").strip()
                if not link or not title or link in seen: continue
                seen.add(link)
                raw = e.get("published", e.get("updated", ""))
                try:
                    dt = parsedate_to_datetime(raw) if raw else None
                    when = dt.astimezone(timezone.utc).strftime("%d %b %Y %H:%M UTC") if dt else "Date unavailable"
                    stamp = dt.timestamp() if dt else 0
                except Exception:
                    when, stamp = "Date unavailable", 0
                rows.append({"Headline":title,"Source":source,"Published":when,"Link":link,"stamp":stamp})
        except Exception:
            pass
    return sorted(rows, key=lambda r:r["stamp"], reverse=True)

def find_col(df, options):
    return next((c for c in options if c in df.columns), None)

with st.sidebar:
    st.header("BEAST")
    page = st.radio("Dashboard", ["Overview","Predictions","Football News","Upload / Setup"])
    st.caption("Launch build · Model estimates only")

if "predictions" not in st.session_state:
    st.session_state.predictions = None

if page == "Upload / Setup":
    st.subheader("Load your existing predictions")
    st.write("Upload a CSV exported from your Colab `out` DataFrame to populate the app.")
    upload = st.file_uploader("BEAST predictions CSV", type=["csv"])
    if upload:
        try:
            d = pd.read_csv(upload)
            st.session_state.predictions = d
            st.success(f"Loaded {len(d):,} rows.")
            st.dataframe(d.head(15), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
    st.divider()
    st.subheader("Optional: upcoming match predictions")
    st.write("This requires a saved, compatible model and a fixture CSV containing the exact feature columns.")
    st.info("Once you locate the fitted model in Colab, we can connect it. Do not upload API keys or passwords.")

elif page == "Football News":
    st.subheader("Football news desk")
    st.caption("Public RSS headlines, cached for 15 minutes. Click through to the publisher for the full story.")
    if st.button("Refresh headlines"): get_news.clear()
    news = get_news()
    if not news:
        st.warning("Feeds could not be reached. Try again later.")
    else:
        sources = sorted(set(x["Source"] for x in news))
        selected = st.multiselect("Sources", sources, default=sources)
        query = st.text_input("Search headline", placeholder="Team, league, injury...")
        shown = [x for x in news if x["Source"] in selected and query.lower() in x["Headline"].lower()]
        st.caption(f"{len(shown)} headlines")
        for x in shown[:60]:
            st.markdown(f'<div class="news"><b>{x["Headline"]}</b><br><small>{x["Source"]} · {x["Published"]}</small><br><a href="{x["Link"]}" target="_blank">Read story ↗</a></div>', unsafe_allow_html=True)

elif page == "Predictions":
    st.subheader("BTTS predictions")
    d = st.session_state.predictions
    if d is None:
        st.info("Open Upload / Setup and upload your exported `out` CSV first.")
    else:
        prob = find_col(d, ["btts_probability","BTTS_Probability","probability","prob"])
        comp = find_col(d, ["competition","Competition","league"])
        date = find_col(d, ["date","Date","kickoff","datetime"])
        home = find_col(d, ["home_team","HomeTeam","home","Home"])
        away = find_col(d, ["away_team","AwayTeam","away","Away"])
        a,b,c = st.columns(3)
        a.metric("Matches",f"{len(d):,}")
        if prob:
            p = pd.to_numeric(d[prob],errors="coerce")
            b.metric("Average BTTS probability",f"{p.mean():.1%}")
            c.metric("Probability ≥55%",int((p>=.55).sum()))
            threshold = st.slider("Minimum probability",0,90,50)/100
            view = d[p>=threshold].copy()
            if comp:
                comps = sorted(view[comp].dropna().astype(str).unique())
                chosen = st.multiselect("Competitions",comps,default=comps)
                view = view[view[comp].astype(str).isin(chosen)]
            view = view.sort_values(prob,ascending=False)
        else:
            st.warning("No probability column found; showing rows as provided.")
            view = d.copy()
        cols = [x for x in [date,comp,home,away,prob,"prediction","target"] if x and x in view.columns]
        st.dataframe(view[cols] if cols else view,use_container_width=True,hide_index=True)
        st.download_button("Download table as CSV",view.to_csv(index=False).encode(), "beast_predictions_filtered.csv","text/csv")
        st.caption("Probabilities are estimates, not guaranteed outcomes. Check team news, confirmed lineups and current odds.")

else:
    d = st.session_state.predictions
    news = get_news()
    a,b,c,dcol = st.columns(4)
    a.metric("Prediction rows",f"{len(d):,}" if d is not None else "Awaiting CSV")
    b.metric("News headlines",len(news))
    prob = find_col(d,["btts_probability","BTTS_Probability","probability","prob"]) if d is not None else None
    if prob:
        p = pd.to_numeric(d[prob],errors="coerce")
        c.metric("Mean BTTS probability",f"{p.mean():.1%}")
        dcol.metric("Probability ≥55%",int((p>=.55).sum()))
    else:
        c.metric("Model status","Needs data")
        dcol.metric("Live predictions","Not connected")
    left,right = st.columns([1.2,1])
    with left:
        st.subheader("Prediction shortlist")
        if d is None: st.info("Upload your existing predictions CSV under Upload / Setup.")
        elif prob: st.dataframe(d.sort_values(prob,ascending=False).head(10),use_container_width=True,hide_index=True)
        else: st.dataframe(d.head(10),use_container_width=True,hide_index=True)
    with right:
        st.subheader("Latest headlines")
        if not news: st.warning("News feeds temporarily unavailable.")
        for x in news[:8]:
            st.markdown(f'**[{x["Headline"]}]({x["Link"]})**')
            st.caption(f'{x["Source"]} · {x["Published"]}')
    st.divider()
    st.caption("Experimental football decision-support tool. No prediction guarantees a result or profit.")
