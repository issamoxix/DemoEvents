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
        roi_df = roi_df[roi_df["unified_tags"] == tag]
    # if mapstyle == "EventBrite":
        # roi_df = roi_df[roi_df["ticket_availability.maximum_ticket_price.currency"] == "EUR"]
        # st.map(roi_df, color="color", size="average_ticket_price", hex=)
    # else:
    st.map(roi_df, color="color", size=20)

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

    tag_duration = df.groupby("tags1display_name")["event_duration"].mean()
    duration_fig = plt.figure(figsize=(10, 6))
    tag_duration.plot(kind="bar", color="lightgreen")

    plt.title("Average Event Duration by Tags")
    plt.xlabel("Tags")
    plt.ylabel("Average Duration (Days)")
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    st.subheader("Duration Frequency")
    st.markdown(
        """
        This chart shows the average duration of events based on the selected source.
        """
    )
    st.pyplot(duration_fig)

    is_sold_out = {
        "Platform": ["EventBrite", "Eventtim"],
        "Average Sold Out (%)": [5.506607929515418, 0.9],
    }
    sold_out_df = pd.DataFrame(is_sold_out)
    st.subheader("Average Sold Out (%)")
    st.table(sold_out_df)

    with st.echo():
        filepath = "https://raw.githubusercontent.com/issamoxix/DemoEvents/refs/heads/main/data/EventBrite/DataFrame.csv"
        # eventbrite_df["lat"] = eventbrite_df["primary_venue.address.latitude"]
    # eventbrite_df["lon"] = eventbrite_df["primary_venue.address.longitude"]
        m = leafmap.Map(center=[40, -100], zoom=4)
        m.add_heatmap(
            filepath,
            latitude="primary_venue.address.latitude",
            longitude="primary_venue.address.longitude",
            value="average_ticket_price",
            name="Heat map",
            radius=20,
        )


if __name__ == "__main__":
    main()
