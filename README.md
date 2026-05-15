# One Piece TCG Analysis (2026)
## Overview
A data collection, cleaning, and analysis project tracking 180+ days of One Piece Trading Card Game (OPTCG) price history across 19 English version sets. 
[View Interactive Dashboard (Tableau Public)](https://public.tableau.com/shared/G2NWQDKD2?:display_count=n&:origin=viz_share_link)

## Objective
Collect raw OPTCG price data and apply data cleaning, transformation, and analysis techniques to identify and visualize optimal buying windows and price trends for both players and collectors. 

## Data Source
- Source: Data was pulled from the JUSTTCG API using the free tier plan
- Size: 
    - Raw Price History: 6,507,083 total rows (2,872,868 + 3,634,215)
    - Raw Card Variants: 17,836 total rows (8,649 + 9,181)
- Collected: February 4, 2026 & February 15, 2026

## Sets Included
- Main Booster Sets: OP01 - OP14
- Premium Booster Sets: PRB01 & PRB02
- Extra Booster Sets: EB01 - EB03

## Key Insights
- Super Rares have the most significant post-launch drop among all base rarities
- Wanted Posters are the only rarity variant that consistently increases in value immediately after pre-release
- Wanted Posters, SPs, and Manga Rares maintain a positive price index after the first month of release
- The best buying window is on day 30-60 for Near Mint (NM) cards, Base Rarity cards, and sealed products since prices for the specified products reach their floor in this range when analyzing the most recent sets with existing early price data (OP12-14, PRB02, and EB03)
- Variant-specific buying windows differ:
    - Wanted Posters & Mangas: Day 0-6
    - SPs: Day 7-29
    - Gold Don: Day 60-89

## Tools
|Tool|Purpose|
|----|-------|
|Python|Data collection and cleaning pipeline|
|requests|JustTCG API calls|
|pandas|Data cleaning, transformation, and feature engineering|
|numpy|Numerical operations and vectorized transformations|
|python-dotenv|API key management via .env|
|Jupyter Notebook|Analysis, documentation, and exports|
|Tableau Public|Interactive dashboard|

## Project Structure
|File|Description|
|----|-----------|
|00_check_env.py|Verify API credentials and environment|
|01_test_auth.py|Test API authentication|
|02_find_game_id.py|Locate OPTCG game ID in API|
|03_list_sets.py|Fetch all available sets|
|04_filter_sets.py|Filter to included sets only|
|05_fetch_cards.py|Pull card data from API|
|06_jsonl_to_csv.py|Convert raw JSONL to CSV|
|analysis.ipynb|Full cleaning, feature engineering, and analysis|
|requirements.txt|Python dependencies|
|README.md|Project Overview|

## Pipeline Overview
 ### Step 1: Data Collection (00 - 06)
 - The scripts pull two datasets from the JUSTTCG API:
    - card_variants.csv - metadata for every card variant (card name, set, rarity, condition, release date)
    - price_history.csv - daily price observations per variant
 - Raw responses are saved as .jsonl files then converted to CSV via 06_jsl_to_csv.py
 ### Step 2: Cleaning (analysis.ipynb)
 - Date normalization
    - Parse mixed-format timestamps in price history
    - Standardize all date columns to datetime types
 - Deduplication
    - Remove duplicate rows from both datasets
    - Keep the most revently updated record for card variant duplicates
    - For price history duplicates, deduplicate based on timestamp for each variant_id
 - ID alignment
    - Check for variant IDs present in price history but missing from card variants and vice versa
    - Flag variants with no price history
 - ID shortening
    - Replace long API-generated IDs with human-readable slugs
        - Example: romance-dawn-one-piece-card-game -> OP01
    - Short variant IDs follow the pattern: {set}-{card-name}-{rarity}-{condition}
 ### Step 3: Feature Engineering (analysis.ipynb)
 |Feature|Description|
 |:-----:|:---------:|
 |days_since_release|Days elapsed since the card's set release date|
 |rarity variant|Classified variant type (Normal, Alternate Art, SP, Manga, etc.)|
 |price_index|Price normalized to launch week = 100 for cross-card comparison|
 |baseline_price|Reference price used for indexing|
 |daily_return|Day-over-day percentage price change|
 |7d_return|7-day rolling percentage price change|
 |lifecycle_stage|Bucketed time period based on days since release|
 |obs_day|Sequential observation count per variant|
 |max_days_available:|Total days of price data available per variant|
 #### Rarity Variant Classfication
 |Rarity Variant|Alias|
 |:------------:|:---:|
 |Common|C|
 |Uncommon|UC|
 |DON!!!|Don|
 |Rare|R|
 |Super Rare|SR|
 |Secret Rare|SEC|
 |Treasure Rare|TR|
 |Gold DON!!!|Gold Don|
 |Special Rare/Parallel|SP|
 |Super Alternate Art/Manga Rare|Manga|
 |Silver Special Rare/Parallel|Silver SP|
 |Gold Special Rare/Parallel|Gold SP|
 |Red Super Alternate Art/Red Manga Rare|Red Manga|
 |Wanted Poster|Wanted Poster|
 |Alternate Art/Parallel|Alternate Art|
 |Full Art|Full Art|
 |Textured Foil|Textured Foil|
 #### Lifecycle Stages:
 |Stage|Days Since Release|
 |:---:|:----------------:|
 |Pre-Release|<0|
 |Launch Week|0-6|
 |Early Post-Launch|7-29|
 |Early Phase|30-89|
 |Mid Phase|90-179|
 |Late Phase|180-364|
 |Mature Phase|365+|
 ### Step 4: Milestones Table(analysis.ipynb)
 - A summary table pivots median prices per variant per lifecycle stage and computes:
 |Metric|Description|
 |:----:|:----------|
 |change_pre_to_week_pct|% price change from pre-release to launch week|
 |change_pre_to_month_pct|% price change from pre-release to first month|
 |change_week_to_month_pct|% price change from launch week to first month|
 |week_efficieny_ratio| How much of the total decline happened in launch week vs the full first month|
 ### Step 5: Outputs
 - Export as CSVs for data visualization
 |File|Description|
 |:---:|:--------:|
 |variants_clean.csv|Cleaned table of card variants & metadata|
 |prices_clean.csv|Cleaned price history with all engineered features|
 |milestones.csv|Per-variant lifecycle stage price summary|

## Setup and Usage
### Prerequisites
- Python 3.10+
- Free JustTCG account and API key
### Environment Variables
- Create a .env file in the root directory and insert: JUSTTCG_API_KEY=your_unique_justtcg_api_key
### Running the Pipeline
#### Data Collection
Run Python scripts 00 - 06 in order
- Assign a unique name to "OUT_FILE" in 05 for version control
- Assing unique names to "VARIANTS_OUT" and "HISTORY_OUT" in 06 for version control. Keep these files as they contain the earliest start point for your data
#### Data Analysis
Open analysis.ipynb to clean, process, engineer features, analyze, and export final CSVs
##### Overhead Section
- Assign "variants" and "prices" as the variants and price history output files in 06
##### Export CSVs: Sort Tables & Export Section
- Assign unique names to "VARIANTS_OUT" and "PRICES_OUT" for version control. Names should indicate that files are cleaned
##### Building more features Section
- In the Set Up Section, assign "variants" and "prices" to the respective cleaned variants and price history files from the Export CSVs section
- In the Sort and Export Section, assign unique names to "VARIANTS_OUT", "PRICES_OUT", and "MILESTONES_OUT" for version control. Best to indicate that these files have been cleaned with added features. These files will then be used in Tableau for visualization. 
##### Appending CSVs Section
Run Python scripts 00 - 06 at a future date to expand dataset
- Assign "variants_1" as the initial 06 "VARIANTS_OUT" file, and "variants_2" as the most recent 06 "VARIANTS_OUT" file
- Assign "prices_1" as the initial 06 "HISTORY_OUT" file, and "prices_2" as the most recent 06 "HISTORY_OUT" file
- "source_number_1" and "source_number_2" should be the "variants_1"/"prices_1" and "variants_2"/"prices_2" respective version number
- "variants_clean.to_csv" and "prices_clean.to_csv" should be named to reflect which "VARIANTS_OUT" and "PRICES_OUT" versions were used
   - I didn't name these files this way when I was initially doing this project, but I wish I did as it would've made identifying files a lot easier
- Assign "variants_clean.to_csv" and "prices_clean.to_csv" to "variants" and "prices" in the Overhead section, respectively, and run the program again to get an updated cleaned dataset

## Important notes for reproducing this project
- The free tier is sufficient for this project with strategic timing
- The daily API request limit resets at 4pm MST
- At the time of completing the project, the JUSTTCG API can only collect the past 180 days of price data at most
- Due to the daily limit, you will need to run the pipleline twice in one day to collect price data from the sets listed above (unless you intend on purchasing a higher tier plan)
- Recommended approach: run the pipeline once in the morning or just before the 4pm reset, then again after 4pm within the same day
- You can exceed the 180 days of price history by repeating the above process at a future date, which will give you deeper insights over time
- Since this project pulls the last 180 days of price history at time of running, your results will differ from the original analysis as new price data becomes available
- Data was pulled on February 4, 2026 and February 15, 2026 for this project, so results, especially for early card prices and buying windows, will be different
- OP12, OP13, OP14, PRB02, EB03, and OP14 card data were used to determine early card prices, buying windows, and set behaviour
- I omitted the Red Manga rarity variant, which was introduced in OP13, because this rarity variant had an abnormally high price index with a very small sample size in comparison to the other high rarity variants
- I only collected card data for cards obtainable in english set releases; so non-english cards and cards from prizes, promotional packs, magazines, and sets, participation packs, starter decks, etc. are not considered in the data analysis