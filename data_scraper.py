import pandas as pd
import eurostat

def fetch_eu_air_traffic(filename="Do not save", year=2022):
	print("1. Fetching Eurostat Air Traffic Data...")
	# Dataset 'avia_paocc' = Passenger transport by partner country
	# Note: Eurostat datasets are massive. We download it and filter it.
	dataset_code = 'avia_paocc'
	
	try:
		df = eurostat.get_data_df(dataset_code)
		year_col = str(year)
		if year_col in df.columns:
			# Filter columns: reporting country (geo), partner country (partner), and traffic
			df_traffic = df[['geo\\TIME_PERIOD', 'partner', year_col]].dropna()
			df_traffic.rename(columns={'geo\\TIME_PERIOD': 'Origin', 'partner': 'Destination', year_col: 'Passengers'}, inplace=True)
			print(f"   -> Successfully found {len(df_traffic)} traffic records.")

			# 1. Drop rows where traffic is zero or missing (NaN)
			df_clean = df_traffic[df_traffic['Passengers'] > 0]

			# 2. Filter out geopolitical aggregates (EU27_2020, EA19, etc.)
			# Eurostat country codes are exactly 2 letters long (e.g., 'SI', 'FR', 'DE').
			df_clean = df_clean[
				(df_clean['Origin'].str.len() == 2) & 
				(df_clean['Destination'].str.len() == 2)
			]

			# Remove domestic flights (where Origin and Destination are the same country)
			df_clean = df_clean[df_clean['Origin'] != df_clean['Destination']]

			print(f"   -> After cleanup succesfully loaded {len(df_traffic)} traffic records.")
			# Use pivot_table to create the matrix
			# Origin becomes the Y-axis (index), Destination becomes the X-axis (columns)
			traffic_matrix = pd.pivot_table(
				df_clean, 
				values='Passengers', 
				index='Origin', 
				columns='Destination', 
				aggfunc='sum',     # Sums the passengers if there are duplicate route entries
			)
			
			# This aligns the rows and columns so they match exactly.
			all_countries = sorted(list(set(traffic_matrix.index).union(set(traffic_matrix.columns))))
			traffic_matrix = traffic_matrix.reindex(index=all_countries, columns=all_countries)
			# Sometimes a country only receives flights but doesn't send them (or vice versa in the data).
			imputed_matrix = traffic_matrix.combine_first(traffic_matrix.T)
			final_matrix = imputed_matrix.fillna(0)
			return final_matrix
		else:
			print("   -> Year not found in dataset. Please check Eurostat column names.")
			return None

	except Exception as e:
		print(f"Failed to fetch Eurostat data: {e}")
		return None
	
def fetch_eu_populations(year=2022):
	year_col = str(year)
	print("Fetching Eurostat Population Data...")
	
	# 'demo_pjan' is the official dataset for population on Jan 1st
	dataset_code = 'demo_pjan'
	
	try:
		# Download the raw dataset
		df_pop = eurostat.get_data_df(dataset_code)
		
		# Eurostat demographic data is highly segmented. 
		# We only want: Total Sex ('T') and Total Age ('TOTAL')
		if 'sex' in df_pop.columns and 'age' in df_pop.columns:
			df_pop = df_pop[(df_pop['sex'] == 'T') & (df_pop['age'] == 'TOTAL')]
		
		# Check if our target year exists in the dataset
		if year_col in df_pop.columns:
			# Keep only the country code (geo\time) and the population for that year
			df_clean_pop = df_pop[['geo\\TIME_PERIOD', year_col]].copy()
			df_clean_pop.rename(columns={'geo\\TIME_PERIOD': 'Country_Code', year_col: 'Population'}, inplace=True)
			
			# Filter out the non-country aggregates (e.g., 'EU27_2020', 'EA19')
			# Country codes are exactly 2 characters long
			df_clean_pop = df_clean_pop[df_clean_pop['Country_Code'].str.len() == 2]
			
			print(f"   -> Successfully loaded populations for {len(df_clean_pop)} entities.")
			if df_clean_pop is not None:
				df_clean_pop.set_index("Country_Code")
				return df_clean_pop
		else:
			print(f"   -> Year {year_col} not found in population dataset.")
			return None        
	except Exception as e:
		print(f"Failed to fetch Eurostat population data: {e}")
		return None