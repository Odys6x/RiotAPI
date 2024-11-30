import pandas as pd

df = pd.read_csv("match_results_with_objectives.csv")

print(f"Original number of rows: {len(df)}")

df_cleaned = df[df['game_duration'] >= 300]

df_cleaned = df_cleaned.reset_index(drop=True)

print(f"Number of rows after removing short games: {len(df_cleaned)}")
print(f"Number of rows removed: {len(df) - len(df_cleaned)}")

df_cleaned.to_csv("cleaned_match_results.csv", index=False)
print("\nCleaned data saved to 'cleaned_match_results.csv'")