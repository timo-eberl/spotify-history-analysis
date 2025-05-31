#!/usr/bin/env python3

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, UTC
import calendar
import pytz
import itertools

# How long the list of top songs/artists/whatever should be
n_top_elements = 10
# Filter to only the last x days
history_days = int(365 * 1)
# Optional date until the data should be filtered
last_date = None # e.g. "2024-12-31"

def load_spotify_history(directory='.'):
    history = []

    # Loop through all files in the given directory
    for filename in os.listdir(directory):
        if filename.startswith("Streaming_History_Audio_") and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    if isinstance(data, list):
                        history.extend(data)
                    else:
                        print(f"Warning: Unexpected format in {filename}")
                except json.JSONDecodeError as e:
                    print(f"Error reading {filename}: {e}")

    return history

def filter_history_by_date(history, start_date, end_date):
    """
    Filters history to only include entries between start_date and end_date (inclusive).
    Dates should be in 'YYYY-MM-DD' format.
    """
    filtered = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    for entry in history:
        ts_str = entry.get("ts")
        if ts_str:
            try:
                ts_dt = datetime.strptime(ts_str[:10], "%Y-%m-%d")
                if start_dt <= ts_dt <= end_dt:
                    filtered.append(entry)
            except ValueError:
                continue  # skip malformed timestamps

    return filtered

def get_latest_date(history):
    latest_dt = None
    for entry in history:
        ts = entry.get("ts")
        if ts:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                if (latest_dt is None) or (dt > latest_dt):
                    latest_dt = dt
            except ValueError:
                continue
    return latest_dt

def total_listening_time(history):
    """
    Returns total listening time in minutes.
    """
    total_ms = sum(entry.get("ms_played", 0) for entry in history if entry.get("ms_played", 0) > 0)
    total_minutes = total_ms // 60000
    return total_minutes

def top_songs_by_playtime(history, top_n=5):
    playtime_by_song = defaultdict(int)

    for entry in history:
        track = entry.get("master_metadata_track_name")
        artist = entry.get("master_metadata_album_artist_name")
        ms_played = entry.get("ms_played", 0)

        if track and artist:
            key = f"{track} by {artist}"
            playtime_by_song[key] += ms_played

    # Sort by total playtime descending
    top_songs = sorted(playtime_by_song.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Convert milliseconds to minutes for display
    return [(song, round(ms / 60000, 2)) for song, ms in top_songs]

def top_songs_by_playcount(history, top_n=5):
    count_by_song = defaultdict(int)

    for entry in history:
        # Skip entries that were marked as skipped
        if entry.get("skipped", False):
            continue

        track = entry.get("master_metadata_track_name")
        artist = entry.get("master_metadata_album_artist_name")

        if track and artist:
            key = f"{track} by {artist}"
            count_by_song[key] += 1

    top_songs = sorted(count_by_song.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return top_songs

def top_songs_incognito(history, top_n=5, by_playtime=True):
    stat_by_song = defaultdict(int)

    for entry in history:
        if entry.get("incognito_mode") is True:
            track = entry.get("master_metadata_track_name")
            artist = entry.get("master_metadata_album_artist_name")
            if track and artist:
                key = f"{track} by {artist}"
                if by_playtime:
                    stat_by_song[key] += entry.get("ms_played", 0)
                else:
                    stat_by_song[key] += 1

    top_songs = sorted(stat_by_song.items(), key=lambda x: x[1], reverse=True)[:top_n]

    if by_playtime:
        return [(song, round(ms / 60000, 2)) for song, ms in top_songs]
    else:
        return top_songs

def most_skipped_songs(history, top_n=5):
    skip_count_by_song = defaultdict(int)

    for entry in history:
        if entry.get("skipped") is True:
            track = entry.get("master_metadata_track_name")
            artist = entry.get("master_metadata_album_artist_name")

            if track and artist:
                key = f"{track} by {artist}"
                skip_count_by_song[key] += 1

    top_skipped = sorted(skip_count_by_song.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return top_skipped

def top_artists_by_playtime(history, top_n=5):
    playtime_by_artist = defaultdict(int)

    for entry in history:
        artist = entry.get("master_metadata_album_artist_name")
        ms_played = entry.get("ms_played", 0)

        if artist:
            playtime_by_artist[artist] += ms_played

    top_artists = sorted(playtime_by_artist.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(artist, round(ms / 60000, 2)) for artist, ms in top_artists]

def top_listening_streaks(history, max_gap_minutes=30, top_n=3):
    plays = []
    for entry in history:
        ts_str = entry.get("ts")
        ms_played = entry.get("ms_played", 0)
        if ts_str and ms_played > 0:
            try:
                start_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                end_dt = start_dt + timedelta(milliseconds=ms_played)
                plays.append((start_dt, end_dt))
            except ValueError:
                continue

    plays.sort(key=lambda x: x[0])
    max_gap = timedelta(minutes=max_gap_minutes)

    streaks = []
    current_start = None
    current_end = None

    for start, end in plays:
        if current_end is None:
            current_start = start
            current_end = end
        else:
            gap = start - current_end
            if gap <= max_gap:
                current_end = max(current_end, end)
            else:
                streaks.append((current_start, current_end))
                current_start = start
                current_end = end

    # Add final streak
    if current_start and current_end:
        streaks.append((current_start, current_end))

    # Sort by duration, descending
    streaks.sort(key=lambda s: s[1] - s[0], reverse=True)
    top_streaks = streaks[:top_n]

    def format_duration(td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    result = []
    for i, (start, end) in enumerate(top_streaks, 1):
        duration = end - start
        result.append({
            "rank": i,
            "duration": format_duration(duration),
            "start": start.strftime("%Y-%m-%d %H:%M"),
            "end": end.strftime("%Y-%m-%d %H:%M")
        })

    return result


def count_streaks_longer_than(history, min_duration_minutes=60, max_gap_minutes=30):
    plays = []
    for entry in history:
        ts_str = entry.get("ts")
        ms_played = entry.get("ms_played", 0)
        if ts_str and ms_played > 0:
            try:
                start_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                end_dt = start_dt + timedelta(milliseconds=ms_played)
                plays.append((start_dt, end_dt))
            except ValueError:
                continue
    
    plays.sort(key=lambda x: x[0])
    max_gap = timedelta(minutes=max_gap_minutes)
    min_duration = timedelta(minutes=min_duration_minutes)
    
    streaks = []
    current_streak_start = None
    current_streak_end = None
    
    for start, end in plays:
        if current_streak_end is None:
            current_streak_start = start
            current_streak_end = end
        else:
            gap = start - current_streak_end
            if gap <= max_gap:
                if end > current_streak_end:
                    current_streak_end = end
            else:
                streak_duration = current_streak_end - current_streak_start
                streaks.append(streak_duration)
                current_streak_start = start
                current_streak_end = end
    
    # Add last streak
    if current_streak_end and current_streak_start:
        streak_duration = current_streak_end - current_streak_start
        streaks.append(streak_duration)
    
    # Filter streaks longer than min_duration
    long_streaks = [s for s in streaks if s >= min_duration]
    count_long_streaks = len(long_streaks)
    
    def format_duration(td):
        total_seconds = td.total_seconds()
        minutes = int(total_seconds // 60)
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m"
    
    return count_long_streaks

def listening_time_by_hour(history):
    """
    Returns a dictionary with hour (0-23) as key and total listening time in minutes as value.
    """
    time_by_hour = defaultdict(int)

    for entry in history:
        ts_str = entry.get("ts")
        ms_played = entry.get("ms_played", 0)

        if ts_str and ms_played > 0:
            try:
                ts_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                hour = ts_dt.hour
                time_by_hour[hour] += ms_played
            except ValueError:
                continue

    # Convert ms to minutes and sort by hour
    return {hour: round(ms / 60000, 2) for hour, ms in sorted(time_by_hour.items())}

def average_listening_time_by_month_of_year(history):
    """
    Returns a dict {month (1-12): average listening time in milliseconds} averaged across all years.
    """
    # {year: {month: total_ms}}
    year_month_playtime = defaultdict(lambda: defaultdict(int))

    for entry in history:
        ts = entry.get("ts")
        ms_played = entry.get("ms_played", 0)
        if ts and ms_played > 0:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                year = dt.year
                month = dt.month
                year_month_playtime[year][month] += ms_played
            except ValueError:
                continue

    # For each month, collect total listening times from all years
    month_totals = defaultdict(list)

    for year, months in year_month_playtime.items():
        for month in range(1, 13):
            if month in months:
                month_totals[month].append(months[month])

    # Calculate average per month across years
    avg_per_month = {}
    for month in range(1, 13):
        plays = month_totals.get(month, [])
        if plays:
            avg_ms = sum(plays) / len(plays)
        else:
            avg_ms = 0
        avg_per_month[month] = avg_ms

    return dict(sorted(avg_per_month.items()))

def favorite_song_per_month(history):
    """
    Returns a dict of {month: (song, total_minutes)} for each complete month in the history,
    excluding the earliest (possibly incomplete) month.
    """
    monthly_song_playtime = defaultdict(lambda: defaultdict(int))

    for entry in history:
        ts = entry.get("ts")
        ms_played = entry.get("ms_played", 0)
        track = entry.get("master_metadata_track_name")
        artist = entry.get("master_metadata_album_artist_name")

        if ts and track and artist and ms_played > 0:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                month_key = dt.strftime("%Y-%m")
                song_key = f"{track} by {artist}"
                monthly_song_playtime[month_key][song_key] += ms_played
            except ValueError:
                continue

    # Sort months chronologically
    sorted_months = sorted(monthly_song_playtime.keys())

    favorite_per_month = {}
    for month in sorted_months:
        song_data = monthly_song_playtime[month]
        favorite_song = max(song_data.items(), key=lambda x: x[1])
        song_name, total_ms = favorite_song
        favorite_per_month[month] = (song_name, round(total_ms / 60000, 2))

    return favorite_per_month

def unique_artists_and_songs_per_month(history):
    data = defaultdict(lambda: {'artists': set(), 'songs': set()})

    for record in history:
        ts = record.get('ts')
        if not ts:
            continue
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(pytz.UTC)
        month_key = dt.strftime('%Y-%m')

        artist = record.get('master_metadata_album_artist_name')
        song = record.get('master_metadata_track_name')

        if artist:
            data[month_key]['artists'].add(artist)
        if song:
            data[month_key]['songs'].add(song)

    # Convert sets to counts
    counts_per_month = {}
    for month, sets in data.items():
        counts_per_month[month] = {
            'artists': len(sets['artists']),
            'songs': len(sets['songs'])
        }
    return counts_per_month

def top_most_plays_single_day(history, top_n=5):
    plays_by_song_and_day = defaultdict(int)

    for entry in history:
        if entry.get("skipped", False):
            continue

        track = entry.get("master_metadata_track_name")
        artist = entry.get("master_metadata_album_artist_name")
        ts = entry.get("ts")

        if track and artist and ts:
            key = f"{track} by {artist}"
            date = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
            plays_by_song_and_day[(key, date)] += 1

    # Get top `top_n` by play count
    top = sorted(plays_by_song_and_day.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return top

def top_most_plays_single_week(history, top_n=5):
    plays_per_song_week = defaultdict(int)

    for entry in history:
        track = entry.get("master_metadata_track_name")
        artist = entry.get("master_metadata_album_artist_name")
        ts = entry.get("ts")
        skipped = entry.get("skipped", False)

        if track and artist and ts and not skipped:
            dt = datetime.fromisoformat(ts)
            year, week_num, _ = dt.isocalendar()
            key = (f"{track} by {artist}", year, week_num)
            plays_per_song_week[key] += 1

    top_plays = sorted(plays_per_song_week.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return top_plays

def find_songs_listened_together(history, time_window_minutes=30):
    # Sort history by timestamp
    sorted_history = sorted(history, key=lambda x: x["ts"])

    # Prepare song co-occurrence dictionary
    co_occurrence = defaultdict(lambda: defaultdict(int))

    # Convert timestamp strings to datetime objects
    for entry in sorted_history:
        entry["ts"] = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))

    i = 0
    while i < len(sorted_history):
        window_start = sorted_history[i]["ts"]
        window_end = window_start + timedelta(minutes=time_window_minutes)
        window_entries = []

        # Collect all entries within the time window
        j = i
        while j < len(sorted_history) and sorted_history[j]["ts"] <= window_end:
            track = sorted_history[j].get("master_metadata_track_name")
            artist = sorted_history[j].get("master_metadata_album_artist_name")
            if track and artist and not sorted_history[j].get("skipped", False):
                song = f"{track} by {artist}"
                window_entries.append(song)
            j += 1

        # Count co-occurrences
        for song1, song2 in itertools.combinations(set(window_entries), 2):
            co_occurrence[song1][song2] += 1
            co_occurrence[song2][song1] += 1

        i += 1

    # For each song, sort the co-listened songs
    result = {}
    for song, co_songs in co_occurrence.items():
        sorted_co_songs = sorted(co_songs.items(), key=lambda x: x[1], reverse=True)
        result[song] = sorted_co_songs

    return result


if __name__ == "__main__":
    history = load_spotify_history()

    latest_date = get_latest_date(history) # latest recorded date
    if last_date is not None: # last_date can override
        # Parse last_date string into datetime object, assuming no time given
        latest_date = datetime.fromisoformat(last_date)
    if latest_date is None:
        # fallback to current date if no timestamps found
        latest_date = datetime.now(UTC)
    first_date = latest_date - timedelta(days=history_days)

    history = filter_history_by_date(
        history,
        start_date=first_date.strftime("%Y-%m-%d"),
        end_date=latest_date.strftime("%Y-%m-%d")
    )

    print(f"\nHistory analysis from {first_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')} "
      f"({history_days} days, {history_days / 365:.2f} years):")

    total_minutes = total_listening_time(history)
    print(f"\nTotal listening time: {total_minutes:,} minutes ({total_minutes // 60}h {total_minutes % 60}min)")

    print(f"\nTop {n_top_elements} most listened songs by total playtime:")
    for rank, (song, minutes) in enumerate(top_songs_by_playtime(history, n_top_elements), 1):
        print(f"{rank}. {song} - {minutes} min")

    print(f"\nTop {n_top_elements} most listened songs by number of plays (excluding skipped plays):")
    for rank, (song, count) in enumerate(top_songs_by_playcount(history, n_top_elements), 1):
        print(f"{rank}. {song} - {count} plays")

    # print(f"\nTop {n_top_elements} most listened songs in incognito mode by playtime:")
    # for rank, (song, value) in enumerate(top_songs_incognito(history, n_top_elements, by_playtime=True), 1):
    #     print(f"{rank}. {song} - {value} min")

    print(f"\nTop {n_top_elements} most listened songs in incognito mode by play count:")
    for rank, (song, value) in enumerate(top_songs_incognito(history, n_top_elements, by_playtime=False), 1):
        print(f"{rank}. {song} - {value} plays")

    print(f"\nTop {n_top_elements} most skipped songs:")
    for rank, (song, count) in enumerate(most_skipped_songs(history, n_top_elements), 1):
        print(f"{rank}. {song} - {count} skips")

    print(f"\nTop {n_top_elements} artists by total playtime (in minutes):")
    for rank, (artist, minutes) in enumerate(top_artists_by_playtime(history, n_top_elements), 1):
        print(f"{rank}. {artist} - {minutes} min")

    streaks = top_listening_streaks(history, max_gap_minutes=30, top_n=n_top_elements)
    print(f"\nTop {n_top_elements} longest continuous listening streaks (max 30-minute gap):")
    for streak in streaks:
        print(f"{streak['rank']}. Duration: {streak['duration']} | From: {streak['start']} to {streak['end']}")

    print("\nListening streaks over duration thresholds (max 10-minute gap between tracks):")
    print(f"{'Threshold':<12} {'Count':<6}")
    print("-" * 20)
    for hours in range(1, n_top_elements+1):
        min_duration = 60 * hours  # in minutes
        result = count_streaks_longer_than(history, min_duration_minutes=min_duration, max_gap_minutes=10)
        threshold_label = f"{hours}h:{0:02d}m"
        print(f"{threshold_label:<12} {result:<6}")

    print("\nListening time distribution by hour of day:")
    distribution = listening_time_by_hour(history)
    print(f"{'Hour':<6} {'Listening time (min)':<20}")
    print("-" * 30)
    for hour, minutes in distribution.items():
        print(f"{hour:02d}:00  {minutes/history_days:<20}")

    print("\nAverage Listening Time by Month of Year (minutes):")
    avg_distribution = average_listening_time_by_month_of_year(history)
    print(f"{'Month':<10} {'Avg Minutes':<12}")
    print("-" * 24)
    for month in range(1, 13):
        avg_ms = avg_distribution.get(month, 0)
        avg_minutes = round(avg_ms / 60000, 2)
        print(f"{calendar.month_name[month]:<10} {avg_minutes:<12}")

    print(f"\nFavorite song per month:")
    favorites = favorite_song_per_month(history)
    print(f"{'Month':<8} {'Minutes':<10} {'Song'}")
    print("-" * 75)
    for month, (song, minutes) in favorites.items():
        print(f"{month:<8} {minutes:<10} {song}")

    counts_per_month = unique_artists_and_songs_per_month(history)
    print("\nUnique artists and unique songs per month:")
    print(f"{'Month':<8} {'Unique Artists':<15} {'Unique Songs':<12}")
    print("-" * 40)
    for month in sorted(counts_per_month.keys()):
        artists_count = counts_per_month[month]['artists']
        songs_count = counts_per_month[month]['songs']
        print(f"{month:<8} {artists_count:<15} {songs_count:<12}")
    
    favorites = favorite_song_per_month(history)
    counts_per_month = unique_artists_and_songs_per_month(history)

    print(f"\nTop {n_top_elements} most plays of a single song in one day:")
    for (song, day), count in top_most_plays_single_day(history, top_n=n_top_elements):
        print(f"{count} plays of '{song}' on {day}")

    print(f"\nTop {n_top_elements} most plays of a single song in one week:")
    for (song, year, week_num), count in top_most_plays_single_week(history, top_n=n_top_elements):
        print(f"{count} plays of '{song}' in week {week_num} of {year}")

    time_window = 30
    print(f"\nSongs often listened to together (in a {time_window} minute time window) with your top songs (playtime):")
    co_listens = find_songs_listened_together(history, time_window)
    # Print top 3 co-listened songs for a given song
    for rank, (song, minutes) in enumerate(top_songs_by_playtime(history, n_top_elements), 1):
        if song in co_listens:
            print(f"{song}:")
            for other_song, count in co_listens[song][:3]:
                print(f"  - {other_song} ({count} times)")
