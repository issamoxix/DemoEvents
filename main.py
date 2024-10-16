import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import leafmap.foliumap as leafmap

from constants.mapping import mapping


def unify_tags(row, column1, column2, mapping):
    # Try to map tags1display_name to the new unified category
    tag1 = row[column1]
    tag2 = row[column2]

    # Check if the tag from the first column is in the mapping
    if tag1 in mapping:
        return mapping[tag1]

    # If no match found, fall back to the value in the second column
    return tag2


def main():
    st.header("Events in Berlin", divider="gray")
    st.subheader("Visualizing Events in Berlin")

    st.markdown(
        """
        This dataset contains events and their location in Berlin.
        We created an interactive map plot displaying event locations from Eventbrite and Eventime. You can explore the map to see where events are happening and use the sidebar navigation to filter events based on your preferences for a personalized experience.
        """
    )

    eventbrite_df = pd.read_csv("data/EventBrite/DataFrame.csv")
    eventbrite_df["source"] = "EventBrite"
    eventbrite_df["color"] = "#cf663f"
    eventbrite_df["lat"] = eventbrite_df["primary_venue.address.latitude"]
    eventbrite_df["lon"] = eventbrite_df["primary_venue.address.longitude"]

    eventim_df = pd.read_csv("data/Eventim/DataFrame.csv")
    eventim_df["source"] = "Eventim"
    eventim_df["color"] = "#232864"
    eventim_df["lat"] = eventim_df[
        "products0typeAttributes0liveEntertainment0location0geoLocation0latitude"
    ]
    eventim_df["lon"] = eventim_df[
        "products0typeAttributes0liveEntertainment0location0geoLocation0longitude"
    ]

    df = pd.concat([eventbrite_df, eventim_df])

    eventim_df = eventim_df[(eventim_df["lat"] < 53) & (eventim_df["lon"] < 13.5)]
    df = df[(df["lon"] < 13.5) & (df["lat"] < 52.5)]
    # df[
    #     (df["lat"] >= lat_min)
    #     & (df["lat"] <= lat_max)
    #     & (df["lon"] >= lon_min)
    #     & (df["lon"] <= lon_max)
    # ]
    df["unified_tags"] = df.apply(
        lambda row: unify_tags(row, "categories1name", "tags1display_name", mapping),
        axis=1,
    )

    mapstyle = st.sidebar.selectbox(
        "Choose Map Source:",
        options=["All", "EventBrite", "Eventim"],
        format_func=str.capitalize,
    )

    dataframes = {
        "EventBrite": eventbrite_df,
        "Eventim": eventim_df,
        "All": df,
    }

    tag = st.sidebar.selectbox(
        "Choose Map by Tags:",
        options=["All"] + list(mapping.keys()),
        format_func=str.capitalize,
    )

    roi_df = dataframes[mapstyle]
    if tag != "All":
        roi_df = dataframes["All"]
        roi_df = roi_df[roi_df["unified_tags"] == tag]
    st.map(roi_df, color="color", size=20, zoom=10)

    frequent_source = {
        "EventBrite": "tags1display_name",
        "Eventim": "categories1name",
        "All": "unified_tags",
    }
    freq_source = st.sidebar.selectbox(
        "Choose Freq Source:",
        options=["All", "EventBrite", "Eventim"],
        format_func=str.capitalize,
    )

    st.subheader("Categories Frequency")
    st.markdown(
        """
        This chart shows the frequency of categories in the dataset.
        based on the selected source.
"""
    )

    flattened_tags = df[frequent_source[freq_source]].explode()
    item_counts = flattened_tags.value_counts()
    # skip the least 10 records
    item_counts = item_counts[item_counts >= 15]

    fig = plt.figure(figsize=(8, 6))
    sns.barplot(x=item_counts.values, y=item_counts.index, palette="viridis")
    plt.title("Frequency of Categories")
    plt.xlabel("Events Count")
    plt.ylabel("Categories")
    st.pyplot(fig)

    # average event duration by tags
    st.subheader("Duration Frequency by Tags")
    st.markdown(
        """
        This chart shows the average duration of events based on the selected source.
        """
    )

    tag_duration = df.groupby("tags1display_name")["event_duration"].mean()
    duration_fig = plt.figure(figsize=(10, 6))
    tag_duration.plot(kind="bar", color="#cf663f")

    plt.title("EventBrite Average Event Duration by Tags")
    plt.xlabel("Tags")
    plt.ylabel("Average Duration (Days)")
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    st.pyplot(duration_fig)

    _eventim_tag_duration = df.groupby("categories1name")["event_duration"].mean()

    _eventim_tag_duration_fig = plt.figure(figsize=(10, 6))
    _eventim_tag_duration.plot(kind="bar", color="#232864")

    plt.title("Eventim Average Event Duration by Tags")
    plt.xlabel("Tags")
    plt.ylabel("Average Duration (Days)")
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    st.pyplot(_eventim_tag_duration_fig)

    is_sold_out = {
        "Platform": ["EventBrite", "Eventtim"],
        "Average Sold Out (%)": [5.506607929515418, 0.9],
        "Online Events (%)": [24, None],
    }
    sold_out_df = pd.DataFrame(is_sold_out)
    st.subheader("Average Sold Out (%) and Online Events (%)")
    st.table(sold_out_df)

    eventbrite_df.groupby("primary_venue.name").count()

    st.subheader("Top 10 Venues with Most Events")
    st.markdown(
        """
        This dashboard provides insights into the most popular event venues, helping organizers identify key locations for hosting events. The displayed table showcases the top 10 venues based on event counts, excluding the most prominent venue. This information aids in understanding venue preferences and trends, enabling data-driven decisions for future event planning.
"""
    )
    cols = st.columns(2)

    eventbrite_df["Venue"] = eventbrite_df["primary_venue.name"]
    eventim_df["Venue"] = eventim_df[
        "products0typeAttributes0liveEntertainment0location0name"
    ]

    with cols[0]:
        st.html("<h5 style='color:#cf663f;'>EventBrite</h5>")
        if tag != "All":
            venue_counts = (
                df[(df["source"] == "EventBrite") & (df["unified_tags"] == tag)]
                .groupby("primary_venue.name")
                .size()
            )
            venue_counts.index.name = "Venue"
        else:
            venue_counts = eventbrite_df.groupby("Venue").size()
        sorted_vanues = venue_counts.sort_values(ascending=False)
        top_10 = sorted_vanues.iloc[1:11]
        top_10_df = top_10.reset_index(name="Count")
        top_10_df.index += 1
        st.table(top_10_df)

    with cols[1]:
        st.html("<h5 style='color:#232864;'>Eventim</h5>")
        if tag != "All":
            _venue_counts = (
                df[(df["source"] == "Eventim") & (df["unified_tags"] == tag)]
                .groupby("products0typeAttributes0liveEntertainment0location0name")
                .size()
            )
            _venue_counts.index.name = "Venue"
        else:
            _venue_counts = eventim_df.groupby("Venue").size()
        _sorted_vanues = _venue_counts.sort_values(ascending=False)
        _top_10 = _sorted_vanues.iloc[1:11]
        print(_top_10, _venue_counts)
        _top_10_df = _top_10.reset_index(name="Count")
        _top_10_df.index += 1
        st.table(_top_10_df)


if __name__ == "__main__":
    main()
