# Spotify History Analysis Script

Analyze your Spotify streaming history - Way cooler than Wrapped!!

## Overview

This Python script generates various statistics and insights, including:

- Top songs by playtime and play count
- Most skipped songs
- Listening streaks (continuous listening sessions)
- Listening time distribution by hour of day and month of year
- Favorite song per month
- Number of unique artists and songs in total and per month
- Top number of plays of a single song on a day and in a week
- Songs often listened to together
- Additional statistics using the Spotify API - Optional, requires developer credentials
  - Top genres by playtime
  - Genres of your top artists

## Requirements

- Python 3.6+

## Usage

1. Request your Spotify **Extended streaming history** on Spotifys [Account privacy page](https://www.spotify.com/us/account/privacy/) - May take a few days (it was one day for me)
    > [!NOTE] The streaming history from "Account data" won't work with this script
2. Download and extract the data. Move all files called `Streaming_History_Audio_***.json` next to this script.
3. Run the script:
    ```bash
    python3 spotify_history_analysis.py
    ```

## Configuration

You can customize the analysis by changing these parameters in the script:

| Parameter         | Description                                                                                                                     | Default Value |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `n_top_elements`  | Number of top items (songs, artists, etc.) to display in output                                                                 | `10`          |
| `history_days`    | Number of days (counting backward from the latest date in your data) to include in the analysis                                 | `365`         |
| `last_date`       | Specify the latest date to use for analysis in `YYYY-MM-DD` format. If it is `None`, the latest date is detected from your data | `None`        |
| `use_spotify_api` | Whether to enable additional data fetching and analysis using the Spotify API. Requires developer credentials (see below).      | `False`       |

## Setup for statistics using Spotify API

Before running the script:

1. Set `use_spotify_api` to `True`
2. Create a Spotify "App" to get a Client ID and Client Secret, described [here](https://developer.spotify.com/documentation/web-api/concepts/apps).
3. Set environment variables for Client ID and Client Secret. You need to repeat this step when reopening your terminal.
   - Windows
       ```bash
       set CLIENT_ID=value
       set CLIENT_SECRET=value
       ```
   - Linux and macOS
       ```bash
       export CLIENT_ID=value
       export CLIENT_SECRET=value
       ```
