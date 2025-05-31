# Spotify Data Analysis Script

Analyze your Spotify streaming history - Way cooler than Wrapped!!

## Overview

This Python script generates various statistics and insights, including:

- Top songs by playtime and play count
- Most skipped songs
- Listening streaks (continuous listening sessions)
- Listening time distribution by hour of day and month of year
- Favorite song per month
- Number of unique artists and songs per month

## Requirements

- Python 3.6+

## Usage

1. Request Spotify Extended streaming history on Spotifys [Account privacy page](https://www.spotify.com/us/account/privacy/) - May take a few days
2. Download and extract the data. Move all files called `Streaming_History_Audio_***.json` next to this script.
3. Run the script:
	```bash
	python3 spotify_history_analyzer.py
	```

## Configuration

You can customize the analysis by changing these parameters in the script:

| Parameter        | Description                                                                                     | Default Value |
| ---------------- | ----------------------------------------------------------------------------------------------- | ------------- |
| `n_top_elements` | Number of top items (songs, artists, etc.) to display in output                                 | `10`          |
| `history_days`   | Number of days (counting backward from the latest date in your data) to include in the analysis | `365`         |
